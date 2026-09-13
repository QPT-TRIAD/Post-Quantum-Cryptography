#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
chmod u+x continuation_v1.28/bin/ceqs-carrier-v128 continuation_v1.28p/bin/ceqs-polycarrier-v128
python3 continuation_v1.28/verify_public.py --config continuation_v1.28/fixture/config.json --frame continuation_v1.28/fixture/case0/trace43_rate3.pf28 --frame continuation_v1.28/fixture/case1/trace43_rate3.pf28 --output continuation_v1.28/public_verification.json
python3 continuation_v1.28p/verify_public.py --config continuation_v1.28p/fixture/config.json --frame continuation_v1.28p/fixture/case0/trace43_rate3.pf2p --frame continuation_v1.28p/fixture/case1/trace43_rate3.pf2p --output continuation_v1.28p/public_verification.json
python3 continuation_v1.28p/check_public_mutations.py
python3 continuation_v1.28/audit_carriers.py
