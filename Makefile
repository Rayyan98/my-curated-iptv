# Makefile for IPTV playlist processing
# Generates working playlists from source M3U files

# Configuration
PYTHON = python3
VENV_DIR = venv
CHECKER_SCRIPT = check_playlist.py
SERVER_SCRIPT = serve_playlist.py

# Input files
PK_INPUT = pk.m3u
IN_INPUT = in.m3u

# Output files
PK_OUTPUT = pk_working.m3u
IN_OUTPUT = in_working.m3u

# Virtual environment
VENV_ACTIVATE = $(VENV_DIR)/bin/activate

# Default target
.PHONY: all
all: $(PK_OUTPUT) $(IN_OUTPUT)

# Create virtual environment and install dependencies
$(VENV_ACTIVATE):
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_ACTIVATE) && pip install requests

# Check Pakistani channels
$(PK_OUTPUT): $(PK_INPUT) $(CHECKER_SCRIPT) $(VENV_ACTIVATE)
	@echo "Processing Pakistani channels..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(PK_INPUT) --quiet
	@echo "Pakistani channels processed: $(PK_OUTPUT)"

# Check Indian channels
$(IN_OUTPUT): $(IN_INPUT) $(CHECKER_SCRIPT) $(VENV_ACTIVATE)
	@echo "Processing Indian channels..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(IN_INPUT) --quiet
	@echo "Indian channels processed: $(IN_OUTPUT)"

# Process Pakistani channels with verbose output
.PHONY: pk-verbose
pk-verbose: $(VENV_ACTIVATE)
	@echo "Processing Pakistani channels (verbose)..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(PK_INPUT)

# Process Indian channels with verbose output
.PHONY: in-verbose
in-verbose: $(VENV_ACTIVATE)
	@echo "Processing Indian channels (verbose)..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(CHECKER_SCRIPT) $(IN_INPUT)

# Start HTTP server for Pakistani playlist
.PHONY: serve-pk
serve-pk: $(PK_OUTPUT)
	@echo "Starting server for Pakistani channels..."
	. $(VENV_ACTIVATE) && $(PYTHON) $(SERVER_SCRIPT)

# Start HTTP server for Indian playlist
.PHONY: serve-in
serve-in: $(IN_OUTPUT)
	@echo "Starting server for Indian channels..."
	@echo "Note: Update serve_playlist.py to specify $(IN_OUTPUT) file"
	. $(VENV_ACTIVATE) && $(PYTHON) $(SERVER_SCRIPT)

# Clean generated files
.PHONY: clean
clean:
	rm -f $(PK_OUTPUT) $(IN_OUTPUT)
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
	@echo "  all          - Process both Pakistani and Indian playlists (default)"
	@echo "  $(PK_OUTPUT)     - Process Pakistani channels only"
	@echo "  $(IN_OUTPUT)     - Process Indian channels only"
	@echo "  pk-verbose   - Process Pakistani channels with verbose output"
	@echo "  in-verbose   - Process Indian channels with verbose output"
	@echo "  serve-pk     - Start HTTP server for Pakistani playlist"
	@echo "  serve-in     - Start HTTP server for Indian playlist"
	@echo "  clean        - Remove generated working playlists"
	@echo "  clean-all    - Remove everything including virtual environment"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Input files: $(PK_INPUT), $(IN_INPUT)"
	@echo "Output files: $(PK_OUTPUT), $(IN_OUTPUT)"

# Check if input files exist
.PHONY: check-inputs
check-inputs:
	@if [ ! -f $(PK_INPUT) ]; then echo "Warning: $(PK_INPUT) not found"; fi
	@if [ ! -f $(IN_INPUT) ]; then echo "Warning: $(IN_INPUT) not found"; fi
	@if [ -f $(PK_INPUT) ] && [ -f $(IN_INPUT) ]; then echo "All input files found"; fi