#!/usr/bin/env bash
[[ ! -d ".venv" ]] && { python3 -m venv .venv; echo "Creating virtual environment in .venv" ;} || echo "Environment exists"
./.venv/bin/python3 -m pip install -r requirements.txt
