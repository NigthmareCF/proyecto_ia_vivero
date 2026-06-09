#!/usr/bin/env bash
set -euo pipefail

tail -F /tmp/qr_test_burst_metrics.log
exec bash
