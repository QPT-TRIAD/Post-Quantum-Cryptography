#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
chmod u+x continuation_v1.27/bin/ceqs-paired-trace-v127 continuation_v1.27b/bin/ceqs-fixed-pair-v127b
python3 continuation_v1.27/verify_public.py --config continuation_v1.27/fixture/config.json --frame continuation_v1.27/fixture/case0/trace43_rate3.pt27 --frame continuation_v1.27/fixture/case1/trace43_rate3.pt27 --output continuation_v1.27/public_verification.json
python3 continuation_v1.27b/verify_public.py --config continuation_v1.27b/fixture/config.json --frame continuation_v1.27b/fixture/case0/trace43_rate3.pf27 --frame continuation_v1.27b/fixture/case1/trace43_rate3.pf27 --output continuation_v1.27b/public_verification.json
python3 continuation_v1.27b/check_public_mutations.py
python3 continuation_v1.27b/audit_results.py
