# Makefile for IPTV playlist processing
# Generates consolidated working playlist from source M3U files

# Configuration
PYTHON = python3
VENV_DIR = ../venv
CHECKER_SCRIPT = ../src/check_playlist.py

# Input/Output
MAIN_DIR = main
EXTENDED_DIR = extended
MAIN_OUTPUT = main_working.m3u
EXTENDED_OUTPUT = extended_working.m3u

# Source URLs
PK_URL = https://iptv-org.github.io/iptv/countries/pk.m3u
IN_URL = https://iptv-org.github.io/iptv/countries/in.m3u
GLOBAL_URL = https://iptv-org.github.io/iptv/index.m3u

# Virtual environment
VENV_ACTIVATE = $(VENV_DIR)/bin/activate

# Default target - process both main and extended
.PHONY: all
all: $(MAIN_OUTPUT) $(EXTENDED_OUTPUT)

# Create virtual environment and install dependencies
$(VENV_ACTIVATE):
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_ACTIVATE) && pip install requests

# Download source playlists
$(MAIN_DIR)/pk.m3u:
	@echo "Downloading Pakistani channels from IPTV-org..."
	@mkdir -p $(MAIN_DIR)
	curl -L -o $(MAIN_DIR)/pk.m3u $(PK_URL)
	@echo "Downloaded: $(MAIN_DIR)/pk.m3u"

$(MAIN_DIR)/in.m3u:
	@echo "Downloading Indian channels from IPTV-org..."
	@mkdir -p $(MAIN_DIR)
	curl -L -o $(MAIN_DIR)/in.m3u $(IN_URL)
	@echo "Downloaded: $(MAIN_DIR)/in.m3u"

# Download extended global playlist
$(EXTENDED_DIR)/global.m3u:
	@echo "Downloading global channels from IPTV-org..."
	@mkdir -p $(EXTENDED_DIR)
	curl -L -o $(EXTENDED_DIR)/global.m3u $(GLOBAL_URL)
	@echo "Downloaded: $(EXTENDED_DIR)/global.m3u"

# Download all source files
.PHONY: download
download: $(MAIN_DIR)/pk.m3u $(MAIN_DIR)/in.m3u $(EXTENDED_DIR)/global.m3u
	@echo "All source playlists downloaded successfully"

# Generate working playlist from main folder only
$(MAIN_OUTPUT): $(MAIN_DIR)/*.m3u $(CHECKER_SCRIPT) $(VENV_ACTIVATE)
	@echo "Processing main playlists..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR) --quiet -w 30 -t 5
	@echo "Main playlist generated: $(MAIN_OUTPUT)"

# Generate working playlist from extended folder (with duplicate filtering)
$(EXTENDED_OUTPUT): $(EXTENDED_DIR)/*.m3u $(MAIN_DIR)/*.m3u $(CHECKER_SCRIPT) $(VENV_ACTIVATE)
	@echo "Processing extended playlists (filtering duplicates from main)..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(EXTENDED_DIR) --quiet -w 30 -t 5 --filter-duplicates $(MAIN_DIR)
	@echo "Extended playlist generated: $(EXTENDED_OUTPUT)"

# Individual targets for convenience
.PHONY: main
main: $(MAIN_OUTPUT)

.PHONY: extended
extended: $(EXTENDED_OUTPUT)

# Process main with verbose output
.PHONY: main-verbose
main-verbose: $(VENV_ACTIVATE)
	@echo "Processing main playlists (verbose)..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR) -w 50 -t 5

# Process extended with verbose output  
.PHONY: extended-verbose
extended-verbose: $(VENV_ACTIVATE)
	@echo "Processing extended playlists (verbose, filtering duplicates from main)..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(EXTENDED_DIR) -w 50 -t 5 --filter-duplicates $(MAIN_DIR)



# Clean generated files
.PHONY: clean
clean:
	rm -f $(MAIN_OUTPUT) $(EXTENDED_OUTPUT) $(MAIN_DIR)/*_working.m3u $(EXTENDED_DIR)/*_working.m3u
	@echo "Cleaned generated working playlists"

# Clean everything including virtual environment
.PHONY: clean-all
clean-all: clean
	rm -rf $(VENV_DIR)
	@echo "Cleaned everything including virtual environment"

# Complete workflow: download and process
.PHONY: fresh
fresh: clean download all
	@echo "Fresh build completed: downloaded sources and generated working playlist"

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all          - Generate both main and extended playlists (default)"
	@echo "  main         - Generate main playlist only (Pakistani + Indian)"
	@echo "  extended     - Generate extended playlist only (Global, minus duplicates)"
	@echo "  download     - Download all source playlists from IPTV-org"
	@echo "  fresh        - Clean, download, and process (complete refresh)"
	@echo "  main-verbose - Process main with verbose output"
	@echo "  extended-verbose - Process extended with verbose output"
	@echo "  clean        - Remove generated working playlists"
	@echo "  clean-all    - Remove everything including virtual environment"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Source URLs:"
	@echo "  Pakistani:   $(PK_URL)"
	@echo "  Indian:      $(IN_URL)"
	@echo "  Global:      $(GLOBAL_URL)"
	@echo ""
	@echo "Folders:"
	@echo "  Main:        $(MAIN_DIR)/ → $(MAIN_OUTPUT)"
	@echo "  Extended:    $(EXTENDED_DIR)/ → $(EXTENDED_OUTPUT)"

# Check if input folders exist
.PHONY: check-inputs
check-inputs:
	@echo "Checking input folders..."
	@if [ ! -d $(MAIN_DIR) ]; then echo "⚠️  $(MAIN_DIR) folder not found"; else echo "✅ $(MAIN_DIR) folder found"; fi
	@if [ ! -d $(EXTENDED_DIR) ]; then echo "⚠️  $(EXTENDED_DIR) folder not found"; else echo "✅ $(EXTENDED_DIR) folder found"; fi
	@echo ""
	@if [ -d $(MAIN_DIR) ]; then \
		echo "📁 $(MAIN_DIR)/ files:"; \
		ls -1 $(MAIN_DIR)/*.m3u 2>/dev/null || echo "  No M3U files found"; \
	fi
	@if [ -d $(EXTENDED_DIR) ]; then \
		echo "📁 $(EXTENDED_DIR)/ files:"; \
		ls -1 $(EXTENDED_DIR)/*.m3u 2>/dev/null || echo "  No M3U files found"; \
	fi