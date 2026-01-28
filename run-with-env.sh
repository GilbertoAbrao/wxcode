#!/bin/bash
# Helper script to run wxcode commands with environment variables from .env

# Load .env file
export $(grep -v '^#' .env | xargs -0)

# Execute command
"$@"
