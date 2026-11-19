#!/bin/sh
# Starts PythonIDE on Linux (needs: sudo apt install python3-tk)
cd "$(dirname "$0")" && exec python3 start.pyw "$@"
