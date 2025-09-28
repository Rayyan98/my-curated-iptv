#!/usr/bin/env python3

import requests
import re
import sys
import argparse
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def parse_m3u_with_metadata(file_path):
    """Parse M3U file and return list of entries with metadata and URLs"""
    entries = []
    current_metadata = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#EXTINF'):
                current_metadata = [line]
            elif line.startswith('#EXTVLCOPT'):
                current_metadata.append(line)
            elif line and not line.startswith('#'):
                # This is a URL
                entries.append({
                    'metadata': current_metadata,
                    'url': line
                })
                current_metadata = []
    
    return entries

def extract_tvg_id(metadata_lines):
    """Extract tvg-id from metadata lines"""
    for line in metadata_lines:
        if line.startswith('#EXTINF'):
            # Look for tvg-id="value" pattern
            match = re.search(r'tvg-id="([^"]*)"', line)
            if match:
                return match.group(1)
    return None

def get_existing_tvg_ids(folder_path):
    """Get all tvg-ids from M3U files in a folder"""
    tvg_ids = set()
    
    if not os.path.exists(folder_path):
        return tvg_ids
    
    for file in os.listdir(folder_path):
        if file.endswith(('.m3u', '.m3u8')):
            file_path = os.path.join(folder_path, file)
            entries = parse_m3u_with_metadata(file_path)
            
            for entry in entries:
                tvg_id = extract_tvg_id(entry['metadata'])
                if tvg_id:
                    tvg_ids.add(tvg_id)
    
    return tvg_ids

def filter_duplicates(entries, existing_tvg_ids, quiet=False):
    """Filter out entries that have tvg-ids already in existing_tvg_ids"""
    filtered_entries = []
    duplicate_count = 0
    
    for entry in entries:
        tvg_id = extract_tvg_id(entry['metadata'])
        
        if tvg_id and tvg_id in existing_tvg_ids:
            duplicate_count += 1
        else:
            filtered_entries.append(entry)
    
    if not quiet and duplicate_count > 0:
        print(f"  Filtered {duplicate_count} duplicate entries based on tvg-id")
    
    return filtered_entries, duplicate_count

def get_source_prefix(filename):
    """Get readable prefix for source file"""
    filename_lower = filename.lower()
    
    # Mapping of filenames to readable prefixes
    prefix_map = {
        'pk.m3u': 'Pakistani',
        'in.m3u': 'Indian', 
        'global.m3u': 'Global'
    }
    
    # Check exact matches first
    if filename in prefix_map:
        return prefix_map[filename]
    
    # Fallback: try partial matches or extract from filename
    for key, prefix in prefix_map.items():
        if key in filename_lower:
            return prefix
    
    # Ultimate fallback: capitalize first part of filename
    base_name = filename.split('.')[0]
    return base_name.capitalize()

def add_source_prefix_to_group_title(metadata_lines, source_prefix):
    """Add source prefix to group-title in metadata lines"""
    modified_lines = []
    
    for line in metadata_lines:
        if line.startswith('#EXTINF') and 'group-title=' in line:
            # Find and modify group-title
            import re
            def replace_group_title(match):
                current_group = match.group(1)
                if current_group and not current_group.startswith(source_prefix):
                    return f'group-title="{source_prefix} {current_group}"'
                elif not current_group:
                    return f'group-title="{source_prefix}"'
                else:
                    return match.group(0)  # Already has prefix
            
            modified_line = re.sub(r'group-title="([^"]*)"', replace_group_title, line)
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)
    
    return modified_lines

def check_url(url, timeout=10, max_retries=3):
    """Check if a URL is accessible with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Set timeout and allow redirects
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            if response.status_code == 200:
                if attempt > 0:
                    return url, f"✓ Working (retry {attempt + 1})", response.status_code
                else:
                    return url, "✓ Working", response.status_code
            elif response.status_code in [301, 302, 307, 308]:
                if attempt > 0:
                    return url, f"✓ Working (redirected, retry {attempt + 1})", response.status_code
                else:
                    return url, "✓ Working (redirected)", response.status_code
            else:
                last_error = f"HTTP {response.status_code}"
                if attempt == max_retries - 1:  # Last attempt
                    return url, f"✗ Failed ({response.status_code}) after {max_retries} tries", response.status_code
                
        except requests.exceptions.Timeout:
            last_error = "Timeout"
            if attempt == max_retries - 1:
                return url, f"✗ Timeout after {max_retries} tries", None
                
        except requests.exceptions.ConnectionError:
            last_error = "Connection Error"
            if attempt == max_retries - 1:
                return url, f"✗ Connection Error after {max_retries} tries", None
                
        except requests.exceptions.RequestException as e:
            last_error = f"Request Error: {str(e)[:30]}"
            if attempt == max_retries - 1:
                return url, f"✗ Error: {str(e)[:30]} after {max_retries} tries", None
                
        except Exception as e:
            last_error = f"Unexpected Error: {str(e)[:30]}"
            if attempt == max_retries - 1:
                return url, f"✗ Unexpected Error: {str(e)[:30]} after {max_retries} tries", None
        
        # Brief pause between retries (except for last attempt)
        if attempt < max_retries - 1:
            time.sleep(0.5)
    
    # Fallback (should not reach here)
    return url, f"✗ Failed after {max_retries} tries ({last_error})", None

def write_filtered_m3u(working_entries, output_file):
    """Write working entries to a new M3U file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for entry in working_entries:
            # Write metadata lines
            for metadata_line in entry['metadata']:
                f.write(metadata_line + "\n")
            # Write URL
            f.write(entry['url'] + "\n")

def process_single_file(file_path, timeout=10, max_retries=3, max_workers=20, quiet=False):
    """Process a single M3U file and return working entries with source info"""
    entries = parse_m3u_with_metadata(file_path)
    working_entries = []
    completed_count = 0
    total_count = len(entries)
    
    # Add original index to entries
    for i, entry in enumerate(entries):
        entry['original_index'] = i
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {executor.submit(check_url, entry['url'], timeout, max_retries): entry for entry in entries}
        
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            url, status, status_code = future.result()
            completed_count += 1
            
            # Show progress every 5 completions for better UX
            if not quiet and completed_count % 5 == 0:
                progress = (completed_count / total_count) * 100
                print(f"    Progress: {completed_count}/{total_count} ({progress:.1f}%)")
            
            if "Working" in status:
                # Add source file info to entry
                entry['source_file'] = os.path.basename(file_path)
                
                # Add source prefix to group-title
                source_prefix = get_source_prefix(entry['source_file'])
                entry['metadata'] = add_source_prefix_to_group_title(entry['metadata'], source_prefix)
                
                working_entries.append(entry)
    
    # Sort by original order
    working_entries.sort(key=lambda x: x['original_index'])
    return working_entries, len(entries)

def main():
    parser = argparse.ArgumentParser(description='Check M3U playlist URLs and create filtered playlist')
    parser.add_argument('input_path', help='Input M3U file or folder containing M3U files')
    parser.add_argument('-o', '--output', help='Output file for working entries (default: auto-detect based on input)')
    parser.add_argument('-w', '--workers', type=int, default=20, help='Number of worker threads (default: 20)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('-r', '--retries', type=int, default=3, help='Max retries for failed URLs (default: 3)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress detailed output')
    parser.add_argument('--filter-duplicates', help='Path to folder containing M3U files to filter duplicates against')
    
    args = parser.parse_args()
    
    # Validate input path
    if not os.path.exists(args.input_path):
        print(f"Error: Input path '{args.input_path}' not found!")
        sys.exit(1)
    
    # Determine if input is file or folder
    if os.path.isfile(args.input_path):
        # Single file mode (backward compatibility)
        input_files = [args.input_path]
        if args.output:
            output_file = args.output
        else:
            base_name = os.path.splitext(args.input_path)[0]
            output_file = f"{base_name}_working.m3u"
    else:
        # Folder mode - find all M3U files
        input_files = []
        for file in os.listdir(args.input_path):
            if file.endswith(('.m3u', '.m3u8')):
                input_files.append(os.path.join(args.input_path, file))
        
        if not input_files:
            print(f"Error: No M3U files found in folder '{args.input_path}'!")
            sys.exit(1)
        
        input_files.sort()  # Sort for deterministic order
        
        if args.output:
            output_file = args.output
        else:
            # Auto-detect output filename based on input folder
            folder_name = os.path.basename(args.input_path.rstrip('/'))
            output_file = f"{folder_name}_working.m3u"
    
    if not args.quiet:
        if len(input_files) == 1:
            print(f"Checking URLs in {input_files[0]}...")
        else:
            print(f"Checking URLs in {len(input_files)} M3U files from {args.input_path}...")
        print("=" * 80)
    
    # Get existing tvg-ids for duplicate filtering if specified
    existing_tvg_ids = set()
    total_filtered_duplicates = 0
    
    if args.filter_duplicates:
        existing_tvg_ids = get_existing_tvg_ids(args.filter_duplicates)
        if not args.quiet:
            print(f"Loaded {len(existing_tvg_ids)} existing tvg-ids for duplicate filtering")
    
    all_working_entries = []
    total_working = 0
    total_failed = 0
    total_entries = 0
    
    # Process each file
    for file_path in input_files:
        if not args.quiet:
            print(f"\nProcessing {os.path.basename(file_path)}...")
        
        # Get all entries from file first
        all_file_entries = parse_m3u_with_metadata(file_path)
        
        # Filter duplicates if specified
        if args.filter_duplicates:
            filtered_entries, duplicate_count = filter_duplicates(all_file_entries, existing_tvg_ids, args.quiet)
            total_filtered_duplicates += duplicate_count
            
            # Write filtered entries to temporary file for processing
            temp_file = f"{file_path}.temp"
            write_filtered_m3u(filtered_entries, temp_file)
            
            # Process the filtered file
            working_entries, file_total = process_single_file(temp_file, args.timeout, args.retries, args.workers, args.quiet)
            
            # Clean up temp file
            os.remove(temp_file)
            
            # Update file_total to reflect original count before filtering
            original_total = len(all_file_entries)
            file_total = original_total
        else:
            working_entries, file_total = process_single_file(file_path, args.timeout, args.retries, args.workers, args.quiet)
        
        file_working = len(working_entries)
        file_failed = file_total - file_working
        
        if not args.quiet:
            print(f"  ✓ Working: {file_working}, ✗ Failed: {file_failed}, Total: {file_total}")
        
        all_working_entries.extend(working_entries)
        total_working += file_working
        total_failed += file_failed
        total_entries += file_total
    
    # Sort all entries by source file then by original order for deterministic output
    all_working_entries.sort(key=lambda x: (x['source_file'], x.get('original_index', 0)))
    
    # Write consolidated M3U file
    write_filtered_m3u(all_working_entries, output_file)
    
    if not args.quiet:
        print("\n" + "=" * 80)
    
    if len(input_files) == 1:
        print(f"Summary for {input_files[0]}:")
    else:
        print(f"Summary for {len(input_files)} files:")
        for file_path in input_files:
            print(f"  • {os.path.basename(file_path)}")
    
    print(f"✓ Working URLs: {total_working}")
    print(f"✗ Failed URLs: {total_failed}")
    print(f"Total URLs: {total_entries}")
    if total_filtered_duplicates > 0:
        print(f"🔄 Filtered duplicates: {total_filtered_duplicates}")
    print(f"Success Rate: {(total_working/total_entries*100):.1f}%")
    print(f"Consolidated playlist written to: {output_file}")
    
    return total_working

if __name__ == "__main__":
    main()