#!/usr/bin/env bash
set -euo pipefail

[[ $# == 1 ]] || {
	echo "Usage: $0 ARMBIAN_DIR" >&2
	exit 1
}
bundle=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
bash "$bundle/install.sh" "$1"
cd -- "$1"
exec ./compile.sh build napi-minimal \
	REVISION="${REVISION:-26.02.0-$(date -u +%Y%m%d.%H%M%S)}"
