#!/usr/bin/env bash
set -euo pipefail

tail -F /tmp/qr_test_results.log
exec bash
