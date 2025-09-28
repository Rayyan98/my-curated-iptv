# My Curated IPTV

A professional IPTV playlist processing system that automatically tests and curates working TV channels from multiple sources. This project consolidates Pakistani, Indian, and global IPTV channels into verified, working playlists that can be used with any IPTV-compatible application.

## 📺 Usage

### Ready-to-Use Playlist URLs

The following URLs provide direct access to curated, working IPTV playlists:

#### Main Playlist (Pakistani + Indian Channels)
```
https://raw.githubusercontent.com/Rayyan98/my-curated-iptv/refs/heads/main/real_data/main_working.m3u
```
- **361 verified channels** from Pakistan and India
- Focus on regional content including news, entertainment, movies, and religious programming
- Channels include popular networks like Aaj Tak, GEO News, ARY Digital, and more
- Group titles prefixed with "Pakistani" or "Indian" for easy organization

#### Extended Playlist (Global Channels)
```
https://raw.githubusercontent.com/Rayyan98/my-curated-iptv/refs/heads/main/real_data/extended_working.m3u
```
- **6,058 verified channels** from around the world
- Comprehensive international coverage including US, UK, European, Asian, and other global channels
- Excludes duplicate channels already present in the main playlist
- Group titles prefixed with "Global" for easy identification
- Includes diverse categories: news, sports, movies, documentaries, kids, music, and more

### Channel Categories & Content

Both playlists include channels across these categories:
- **News**: International and regional news channels
- **Entertainment**: Movies, series, and general entertainment
- **Sports**: Live sports and sports news
- **Kids**: Children's programming and cartoons  
- **Music**: Music videos and audio channels
- **Religious**: Spiritual and religious content
- **Documentaries**: Educational and factual programming
- **Shopping**: Home shopping and product channels

### How to Use

1. **Copy the playlist URL** you want to use from above
2. **Open your IPTV app** (VLC, Kodi, IPTV Smarters, TiviMate, etc.)
3. **Add the playlist URL** as a new playlist source
4. **Enjoy verified, working channels** that are automatically updated

### IPTV App Compatibility

These M3U playlists work with any standard IPTV application including:
- **VLC Media Player**
- **Kodi** (with IPTV Simple Client)
- **IPTV Smarters Pro**
- **TiviMate**
- **Perfect Player**
- **GSE Smart IPTV**
- **And many more...**

### Update Frequency

Playlists are automatically verified and updated to ensure:
- ✅ All URLs are tested and working
- ✅ Dead links are removed
- ✅ Duplicate channels are consolidated
- ✅ Multiple backup URLs per channel are tested
- ✅ Source prefixes help organize content

---

## 🛠️ Development

### System Architecture

This project implements a sophisticated IPTV playlist processing pipeline with the following key features:

#### Core Processing Engine
The heart of the system is `src/check_playlist.py`, which implements:

```python
# Cross-file tvg-id grouping with backup URL support
def group_entries_by_tvg_id(entries):
    """Group entries by tvg-id, preserving order and metadata"""
    # Groups channels across multiple files by tvg-id
    # Supports multiple URLs per channel for backup links
    
def check_urls_for_group(group_data, timeout=10, max_retries=3):
    """Check URLs for a tvg-id group and return first working URL"""
    # Tests URLs in order, returns first working URL
    # Implements retry logic with exponential backoff
```

#### Input Parameters
The `check_playlist.py` script accepts these parameters:
- **`input_path`** (required): M3U file or folder containing M3U files
- **`-o, --output`**: Output file (default: auto-detected)
- **`-w, --workers`**: Worker threads (default: 20, max: 50)
- **`-t, --timeout`**: Request timeout in seconds (default: 10)
- **`-r, --retries`**: Max retries for failed URLs (default: 3)
- **`-q, --quiet`**: Suppress detailed output
- **`--filter-duplicates`**: External duplicate filtering against another folder

### Project Structure

```
my-curated-iptv/
├── src/
│   ├── check_playlist.py          # Main processing engine
│   └── Makefile.inc              # Shared build logic
├── test_data/                    # Development environment
│   ├── Makefile                  # Test environment wrapper
│   ├── main/                     # Test Pakistani/Indian sources
│   │   ├── pk.m3u               # Mock Pakistani channels
│   │   └── in.m3u               # Mock Indian channels
│   ├── extended/                 # Test global sources
│   │   └── global.m3u           # Mock global channels
│   ├── main_working.m3u         # Test output
│   ├── extended_working.m3u     # Test output
│   └── mock_downloads.sh        # Test data generator
├── real_data/                   # Production environment
│   ├── Makefile                 # Production environment wrapper
│   ├── main/                    # Real Pakistani/Indian sources
│   │   ├── pk.m3u              # IPTV-org Pakistani channels
│   │   └── in.m3u              # IPTV-org Indian channels
│   ├── extended/                # Real global sources
│   │   └── global.m3u          # IPTV-org global channels
│   ├── main_working.m3u        # Production main output
│   └── extended_working.m3u    # Production extended output
├── venv/                       # Python virtual environment
└── README.md                   # This file
```

### Advanced Features

#### Cross-File Channel Consolidation
The system automatically groups channels by `tvg-id` across multiple source files:

```python
# Example: MockPK1 appears in both pk.m3u and in.m3u
# System tests both URLs and keeps the first working one
```

#### Backup URL Support
When multiple URLs exist for the same `tvg-id`, the system:
1. Tests URLs in original file order
2. Returns first working URL
3. Preserves metadata from first occurrence
4. Applies source prefix based on working URL's source file

#### Parallel Processing with GIL Optimization
Uses `ThreadPoolExecutor` optimized for I/O-bound HTTP requests:
- Network requests release Python's GIL during socket operations
- Configurable worker threads (default: 20, production: 50)
- Progress reporting every 5 completions
- Comprehensive timing diagnostics

#### Source Attribution System
Automatically prefixes group-titles based on source:
```python
def get_source_prefix(filename):
    prefix_map = {
        'pk.m3u': 'Pakistani',
        'in.m3u': 'Indian', 
        'global.m3u': 'Global'
    }
```

### Build System

#### Make-Based Architecture
The project uses a sophisticated Makefile system with environment separation:

**Shared Logic** (`src/Makefile.inc`):
```makefile
# Source URLs from IPTV-org
PK_URL = https://iptv-org.github.io/iptv/countries/pk.m3u
IN_URL = https://iptv-org.github.io/iptv/countries/in.m3u
GLOBAL_URL = https://iptv-org.github.io/iptv/index.m3u

# Processing targets
main: $(MAIN_OUTPUT)           # Pakistani + Indian channels
extended: $(EXTENDED_OUTPUT)   # Global channels (minus duplicates)
main-verbose: ...              # With detailed progress logging
extended-verbose: ...          # With detailed progress logging
```

**Environment Wrappers**:
- `test_data/Makefile`: Development environment with mock data
- `real_data/Makefile`: Production environment with real IPTV sources

#### Available Make Targets

| Target | Description |
|--------|-------------|
| `all` | Process both main and extended playlists |
| `main` | Generate main playlist (Pakistani + Indian) |
| `extended` | Generate extended playlist (Global, minus duplicates) |
| `main-verbose` | Process main with detailed logging |
| `extended-verbose` | Process extended with detailed logging |
| `download` | Download all source playlists from IPTV-org |
| `fresh` | Clean, download, and process (complete refresh) |
| `clean` | Remove generated working playlists |
| `clean-all` | Remove everything including virtual environment |

### Testing Strategy

#### Multi-Environment Testing
The project implements comprehensive testing using:

**Mock Data Testing** (`test_data/`):
- Uses `httpbin.org` endpoints for predictable HTTP responses
- Tests various scenarios: working URLs, failures, timeouts, redirects
- Validates cross-file consolidation with controlled duplicate `tvg-id`s
- Verifies backup URL functionality

**Integration Testing** (`real_data/`):
- Tests against real IPTV-org data sources
- Validates performance with large datasets (20,000+ URLs)
- Confirms production-level processing capabilities

#### Test Coverage Areas
1. **URL Testing**: HTTP status codes, timeouts, retries
2. **Cross-File Grouping**: Channel consolidation across sources
3. **Backup URLs**: Multiple URL testing per channel
4. **Duplicate Filtering**: External duplicate detection
5. **Source Prefixes**: Group-title formatting
6. **Parallel Processing**: ThreadPoolExecutor efficiency
7. **Make System**: Build reproducibility

### Data Sources

#### IPTV-org Integration
The project uses curated sources from [IPTV-org](https://github.com/iptv-org/iptv):
- **Pakistani Channels**: ~45 channels from Pakistan
- **Indian Channels**: ~533 channels from India  
- **Global Channels**: ~20,000+ channels worldwide

#### Source Quality Assurance
- Automatic URL validation with retry logic
- HTTP HEAD requests for efficient testing
- Configurable timeout and retry parameters
- Success rate tracking and reporting

### Performance Characteristics

#### Processing Metrics
- **Main Playlist**: ~578 URLs → 361 working (62.6% success rate)
- **Extended Playlist**: ~20,000 URLs → 6,058 working (varies)
- **Processing Speed**: ~50 URLs/second with 50 workers
- **Memory Usage**: Optimized for large datasets

#### Optimization Features
- Parallel HTTP requests with thread pooling
- Efficient M3U parsing with metadata preservation
- Deterministic output ordering
- Progress reporting for long-running operations

### Contributing

#### Development Setup
```bash
# Clone repository
git clone https://github.com/Rayyan98/my-curated-iptv.git
cd my-curated-iptv

# Test with mock data
cd test_data
make main-verbose

# Production processing
cd ../real_data  
make fresh
```

#### Code Standards
- Python 3.x with type hints where beneficial
- Comprehensive error handling and retry logic
- Detailed logging and progress reporting
- Modular design with clear separation of concerns

### Technical Dependencies

- **Python 3.x**: Core runtime
- **requests**: HTTP client for URL testing
- **concurrent.futures**: Parallel processing
- **Make**: Build automation
- **Git**: Version control and deployment

### License & Attribution

This project processes publicly available IPTV streams and provides no guarantees about stream availability or legality. Users are responsible for compliance with local laws and streaming service terms of service.

Data sources are credited to [IPTV-org](https://github.com/iptv-org/iptv) and respective channel providers.