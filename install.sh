#!/usr/bin/env bash
set -euo pipefail

[[ $# == 1 || ( $# == 2 && ${2:-} == --force ) ]] || {
	echo "Usage: $0 ARMBIAN_DIR [--force]" >&2
	exit 1
}

bundle=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
target=$(cd -- "$1" && pwd -P)
[[ -f $target/compile.sh && -d $target/extensions && -d $target/config ]] || {
	echo "Expected an Armbian build directory." >&2
	exit 1
}
[[ -f $target/config/boards/napi-c.csc || -f $target/config/boards/napi-c.conf ]] || {
	echo "NAPI-C board configuration is missing." >&2
	exit 1
}
[[ ! -e $target/userpatches/config-napi-minimal.conf.sh ]] || {
	echo "Conflicting profile: userpatches/config-napi-minimal.conf.sh" >&2
	exit 1
}

sources=(
	config/cleanup/napi-c.conf
	extensions/napi-minimal.sh
	tools/clean-napi-image.sh
	tools/clean-napi-firmware.py
	profiles/napi-minimal.conf
)
destinations=(
	config/cleanup/napi-c.conf
	extensions/napi-minimal.sh
	tools/clean-napi-image.sh
	tools/clean-napi-firmware.py
	userpatches/config-napi-minimal.conf
)
modes=(644 644 755 755 644)

# Check all destinations before changing files.
for index in "${!sources[@]}"; do
	destination=$target/${destinations[$index]}
	case $(realpath -m -- "$destination") in
		"$target"/*) ;;
		*) echo "Destination escapes the build directory: $destination" >&2; exit 1 ;;
	esac
	[[ ! -L $destination && ! -d $destination ]] || {
		echo "Expected a regular destination file: $destination" >&2
		exit 1
	}
	if [[ -e $destination ]] && ! cmp -s -- "$bundle/${sources[$index]}" "$destination"; then
		[[ ${2:-} == --force ]] || {
			echo "File differs: $destination" >&2
			echo "Use --force to back up and replace changed files." >&2
			exit 1
		}
	fi
done

stamp=$(date -u +%Y%m%dT%H%M%S.%N)
for index in "${!sources[@]}"; do
	destination=$target/${destinations[$index]}
	if [[ -f $destination ]] && cmp -s -- "$bundle/${sources[$index]}" "$destination"; then
		continue
	fi
	mkdir -p -- "$(dirname -- "$destination")"
	if [[ -e $destination ]]; then
		cp -p -- "$destination" "$destination.bak.$stamp"
	fi
	install -m "${modes[$index]}" -- "$bundle/${sources[$index]}" "$destination"
done
echo "Installed NAPI-C minimal profile in $target"
