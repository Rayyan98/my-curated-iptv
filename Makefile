# Makefile for IPTV playlist processing
# Generates consolidated working playlist from source M3U files

# Configuration
PYTHON = python3
VENV_DIR = venv
CHECKER_SCRIPT = check_playlist.py

# Input/Output
MAIN_DIR = main
MAIN_OUTPUT = main_working.m3u
INDIVIDUAL_OUTPUTS = pk_working.m3u in_working.m3u

# Virtual environment
VENV_ACTIVATE = $(VENV_DIR)/bin/activate

# Default target - consolidated approach
.PHONY: all
all: $(MAIN_OUTPUT)

# Create virtual environment and install dependencies
$(VENV_ACTIVATE):
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_ACTIVATE) && pip install requests

# Generate consolidated working playlist from main folder
$(MAIN_OUTPUT): $(MAIN_DIR)/*.m3u $(CHECKER_SCRIPT) $(VENV_ACTIVATE)
	@echo "Processing all playlists in $(MAIN_DIR) folder..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR) --quiet
	@echo "Consolidated playlist generated: $(MAIN_OUTPUT)"

# Process with verbose output
.PHONY: verbose
verbose: $(VENV_ACTIVATE)
	@echo "Processing all playlists (verbose)..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR)

# Legacy targets for individual files (backward compatibility)
.PHONY: pk-only
pk-only: $(VENV_ACTIVATE)
	@echo "Processing Pakistani channels only..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR)/pk.m3u

.PHONY: in-only  
in-only: $(VENV_ACTIVATE)
	@echo "Processing Indian channels only..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(MAIN_DIR)/in.m3u


# Clean generated files
.PHONY: clean
clean:
	rm -f $(MAIN_OUTPUT) $(INDIVIDUAL_OUTPUTS)
	@echo "Cleaned generated working playlists"

# Clean everything including virtual environment
.PHONY: clean-all
clean-all: clean
	rm -rf $(VENV_DIR)
	@echo "Cleaned everything including virtual environment"

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all          - Generate consolidated playlist from main folder (default)"
	@echo "  $(MAIN_OUTPUT)   - Generate consolidated playlist"
	@echo "  verbose      - Process with verbose output"
	@echo "  pk-only      - Process Pakistani channels only"
	@echo "  in-only      - Process Indian channels only"
	@echo "  clean        - Remove generated working playlists"
	@echo "  clean-all    - Remove everything including virtual environment"
	@echo "  help         - Show this help message"
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