# Makefile for IPTV playlist processing
# Generates consolidated working playlist from source M3U files

# Configuration
PYTHON = python3
VENV_DIR = venv
CHECKER_SCRIPT = check_playlist.py

# Input/Output
MAIN_DIR = main
MAIN_OUTPUT = main_working.m3u

# Source URLs
PK_URL = https://iptv-org.github.io/iptv/countries/pk.m3u
IN_URL = https://iptv-org.github.io/iptv/countries/in.m3u

# Virtual environment
VENV_ACTIVATE = $(VENV_DIR)/bin/activate

# Default target - consolidated approach
.PHONY: all
all: $(MAIN_OUTPUT)

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

# Download both source files
.PHONY: download
download: $(MAIN_DIR)/pk.m3u $(MAIN_DIR)/in.m3u
	@echo "All source playlists downloaded successfully"

# Generate consolidated working playlist from main folder
$(MAIN_OUTPUT): $(MAIN_DIR)/*.m3u $(CHECKER_SCRIPT) $(VENV_ACTIVATE)
	@echo "Processing all playlists in $(MAIN_DIR) folder..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR) --quiet -w 30 -t 5
	@echo "Consolidated playlist generated: $(MAIN_OUTPUT)"

# Process with verbose output
.PHONY: verbose
verbose: $(VENV_ACTIVATE)
	@echo "Processing all playlists (verbose)..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR) -w 30 -t 5



# Clean generated files
.PHONY: clean
clean:
	rm -f $(MAIN_OUTPUT) $(MAIN_DIR)/*_working.m3u
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
	@echo "  all          - Generate consolidated playlist from main folder (default)"
	@echo "  download     - Download source playlists from IPTV-org"
	@echo "  fresh        - Clean, download, and process (complete refresh)"
	@echo "  $(MAIN_OUTPUT)   - Generate consolidated playlist"
	@echo "  verbose      - Process with verbose output"
	@echo "  clean        - Remove generated working playlists"
	@echo "  clean-all    - Remove everything including virtual environment"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Source URLs:"
	@echo "  Pakistani:   $(PK_URL)"
	@echo "  Indian:      $(IN_URL)"
	@echo ""
	@echo "Input folder: $(MAIN_DIR)/"
	@echo "Output file: $(MAIN_OUTPUT)"

# Check if input folder exists
.PHONY: check-inputs
check-inputs:
	@if [ ! -d $(MAIN_DIR) ]; then echo "Warning: $(MAIN_DIR) folder not found"; fi
	@if [ -d $(MAIN_DIR) ]; then \
		echo "Input folder found: $(MAIN_DIR)/"; \
		echo "M3U files:"; \
		ls -1 $(MAIN_DIR)/*.m3u 2>/dev/null || echo "  No M3U files found"; \
	fi