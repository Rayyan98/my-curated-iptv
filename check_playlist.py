#!/usr/bin/env python3

import requests
import re
import sys
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

def check_url(url):
    """Check if a URL is accessible"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Set timeout and allow redirects
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            return url, "✓ Working", response.status_code
        elif response.status_code in [301, 302, 307, 308]:
            return url, "✓ Working (redirected)", response.status_code
        else:
            return url, f"✗ Failed ({response.status_code})", response.status_code
            
    except requests.exceptions.Timeout:
        return url, "✗ Timeout", None
    except requests.exceptions.ConnectionError:
        return url, "✗ Connection Error", None
    except requests.exceptions.RequestException as e:
        return url, f"✗ Error: {str(e)[:50]}", None
    except Exception as e:
        return url, f"✗ Unexpected Error: {str(e)[:50]}", None

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

def main():
    m3u_file = 'pk.m3u'
    output_file = 'pk_working.m3u'
    
    print(f"Checking URLs in {m3u_file}...")
    print("=" * 80)
    
    # Parse M3U file with metadata
    entries = parse_m3u_with_metadata(m3u_file)
    print(f"Found {len(entries)} entries to check\n")
    
    working_count = 0
    failed_count = 0
    working_entries = []
    
    # Check URLs with threading for faster execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_entry = {executor.submit(check_url, entry['url']): entry for entry in entries}
        
        # Process results as they complete
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            url, status, status_code = future.result()
            
            # Parse domain from URL for cleaner display
            try:
                domain = urlparse(url).netloc
            except:
                domain = url[:50]
            
            print(f"{status:<25} | {domain}")
            
            if "Working" in status:
                working_count += 1
                working_entries.append(entry)
            else:
                failed_count += 1
    
    # Write filtered M3U file
    write_filtered_m3u(working_entries, output_file)
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"✓ Working URLs: {working_count}")
    print(f"✗ Failed URLs: {failed_count}")
    print(f"Total URLs: {len(entries)}")
    print(f"Success Rate: {(working_count/len(entries)*100):.1f}%")
    print(f"\nFiltered playlist written to: {output_file}")

if __name__ == "__main__":
    main()