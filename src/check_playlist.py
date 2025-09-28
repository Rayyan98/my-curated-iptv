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

def group_entries_by_tvg_id(entries):
    """Group entries by tvg-id, preserving order and metadata"""
    tvg_groups = {}
    
    for entry in entries:
        tvg_id = extract_tvg_id(entry['metadata'])
        
        if tvg_id:
            if tvg_id not in tvg_groups:
                tvg_groups[tvg_id] = {
                    'tvg_id': tvg_id,
                    'metadata': entry['metadata'],  # Use first occurrence metadata
                    'urls': [],
                    'original_index': entry['original_index']
                }
            tvg_groups[tvg_id]['urls'].append({
                'url': entry['url'],
                'original_index': entry['original_index'],
                'source_file': entry.get('source_file', 'unknown')
            })
        else:
            # Handle entries without tvg-id as individual groups
            unique_key = f"no_tvg_id_{entry['original_index']}"
            tvg_groups[unique_key] = {
                'tvg_id': None,
                'metadata': entry['metadata'],
                'urls': [{'url': entry['url'], 'original_index': entry['original_index'], 'source_file': entry.get('source_file', 'unknown')}],
                'original_index': entry['original_index']
            }
    
    return tvg_groups

def check_urls_for_group(group_data, timeout=10, max_retries=3):
    """Check URLs for a tvg-id group and return first working URL"""
    tvg_id = group_data['tvg_id']
    urls = group_data['urls']
    
    # Try URLs in original order
    for url_data in urls:
        url = url_data['url']
        url_result, status, status_code = check_url(url, timeout, max_retries)
        
        if "Working" in status:
            return {
                'metadata': group_data['metadata'],
                'url': url,
                'tvg_id': tvg_id,
                'original_index': group_data['original_index'],
                'working_url_index': url_data['original_index'],
                'total_urls_for_id': len(urls),
                'status': status
            }
    
    # No working URLs found
    return None

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

def collect_all_entries(input_files):
    """Collect all entries from multiple files with global indexing"""
    all_entries = []
    global_index = 0
    
    for file_path in input_files:
        entries = parse_m3u_with_metadata(file_path)
        
        for entry in entries:
            entry['original_index'] = global_index
            entry['source_file'] = os.path.basename(file_path)
            all_entries.append(entry)
            global_index += 1
    
    return all_entries

def process_all_files(input_files, timeout=10, max_retries=3, max_workers=20, quiet=False):
    """Process multiple M3U files with cross-file tvg-id grouping"""
    # Collect all entries from all files
    all_entries = collect_all_entries(input_files)
    
    # Group entries by tvg-id across all files
    tvg_groups = group_entries_by_tvg_id(all_entries)
    total_groups = len(tvg_groups)
    total_urls = len(all_entries)
    
    if not quiet:
        unique_channels = sum(1 for group in tvg_groups.values() if group['tvg_id'])
        no_tvg_entries = sum(1 for group in tvg_groups.values() if not group['tvg_id'])
        multi_url_channels = sum(1 for group in tvg_groups.values() if len(group['urls']) > 1)
        cross_file_channels = sum(1 for group in tvg_groups.values() if len(set(url['source_file'] for url in group['urls'] if 'source_file' in url)) > 1)
        
        print(f"    Found {unique_channels} unique channels, {no_tvg_entries} entries without tvg-id")
        print(f"    {multi_url_channels} channels have multiple URLs (backup links)")
        print(f"    {cross_file_channels} channels span multiple source files")
        print(f"    Testing {total_groups} channel groups ({total_urls} total URLs) with {max_workers} workers...")
    
    working_entries = []
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_group = {executor.submit(check_urls_for_group, group_data, timeout, max_retries): group_data for group_data in tvg_groups.values()}
        
        for future in as_completed(future_to_group):
            group_data = future_to_group[future]
            result = future.result()
            completed_count += 1
            
            # Show progress every 5 completions for better UX
            if not quiet and completed_count % 5 == 0:
                progress = (completed_count / total_groups) * 100
                print(f"    Progress: {completed_count}/{total_groups} channel groups ({progress:.1f}%)")
            
            if result:
                # Source file info already in entry from collect_all_entries
                # Add source prefix to group-title using the source file from first working URL
                working_url_source = None
                for url_data in group_data['urls']:
                    if url_data['url'] == result['url']:
                        working_url_source = url_data.get('source_file', group_data.get('source_file', 'unknown'))
                        break
                
                if working_url_source:
                    source_prefix = get_source_prefix(working_url_source)
                    result['metadata'] = add_source_prefix_to_group_title(result['metadata'], source_prefix)
                    result['source_file'] = working_url_source
                
                working_entries.append(result)
    
    if not quiet:
        working_channels = len(working_entries)
        print(f"    Result: {working_channels} working channels from {total_groups} channel groups")
    
    # Sort by original order
    working_entries.sort(key=lambda x: x['original_index'])
    return working_entries, total_urls

def process_single_file(file_path, timeout=10, max_retries=3, max_workers=20, quiet=False):
    """Process a single M3U file (backward compatibility)"""
    return process_all_files([file_path], timeout, max_retries, max_workers, quiet)

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
    
    # Handle external duplicate filtering if specified
    existing_tvg_ids = set()
    total_filtered_duplicates = 0
    files_to_process = input_files.copy()
    
    if args.filter_duplicates:
        existing_tvg_ids = get_existing_tvg_ids(args.filter_duplicates)
        if not args.quiet:
            print(f"Loaded {len(existing_tvg_ids)} existing tvg-ids for external duplicate filtering")
        
        # Filter each file separately against external duplicates, then process together
        filtered_files = []
        for file_path in input_files:
            all_file_entries = parse_m3u_with_metadata(file_path)
            filtered_entries, duplicate_count = filter_duplicates(all_file_entries, existing_tvg_ids, args.quiet)
            total_filtered_duplicates += duplicate_count
            
            # Write filtered entries to temporary file
            temp_file = f"{file_path}.temp"
            write_filtered_m3u(filtered_entries, temp_file)
            filtered_files.append(temp_file)
        
        files_to_process = filtered_files
    
    # Process all files with cross-file tvg-id grouping (always enabled)
    if not args.quiet:
        print(f"\nProcessing all files with cross-file channel grouping...")
    
    all_working_entries, total_entries = process_all_files(files_to_process, args.timeout, args.retries, args.workers, args.quiet)
    
    # Clean up temp files if external duplicate filtering was used
    if args.filter_duplicates:
        for temp_file in files_to_process:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    total_working = len(all_working_entries)
    total_failed = total_entries - total_working
    
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