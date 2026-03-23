#!/bin/bash
cd "$(dirname "$0")"
exec .venv/bin/python3 -m hibob_mcp_readonly.server "$@"
