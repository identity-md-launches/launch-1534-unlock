#!/usr/bin/env bash
set -euo pipefail
forge build
python3 scripts/generate_code_checks.py --check
forge test
forge fmt --check
forge lint src --severity high med
python3 scripts/verify_network.py
