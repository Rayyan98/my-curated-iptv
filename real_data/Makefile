# Real Data Makefile - Wrapper for main build logic  
# This allows running 'make' commands from real_data/ directory

# Include the main build logic from src/
include ../src/Makefile.inc

# Override settings for production environment
.PHONY: info
info:
	@echo "🚀 Real Data Environment"
	@echo "Working directory: $(shell pwd)"
	@echo "Source script: $(CHECKER_SCRIPT)"
	@echo "Virtual env: $(VENV_DIR)"
	@echo ""
	@$(MAKE) check-inputs