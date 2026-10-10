function custom_kernel_config__napi_minimal() {
	[[ ${BOARD} == napi-c ]] || return 0
	local -a REMOVE_PACKAGES KEEP_PACKAGES KEEP_FIRMWARE KERNEL_DISABLE KERNEL_ENABLE
	local REMOVE_MAN_PAGES PRUNE_FIRMWARE
	source "${SRC}/config/cleanup/napi-c.conf"
	opts_n+=("${KERNEL_DISABLE[@]}")
	opts_y+=("${KERNEL_ENABLE[@]}")
}

function post_repo_customize_image__990_napi_minimal() {
	[[ ${BOARD} == napi-c ]] || return 0
	display_alert "NAPI-C" "removing configured image packages and files" "info"
	run_host_command_logged bash "${SRC}/tools/clean-napi-image.sh" \
		"${SDCARD}" "${SRC}/config/cleanup/napi-c.conf" --apply
}

function post_post_debootstrap_tweaks__990_napi_minimal_apt_lists() {
 [[ ${BOARD} == napi-c ]] || return 0
 local -a INSTALL_PACKAGES REMOVE_PACKAGES KEEP_PACKAGES KEEP_DOCUMENTATION KEEP_KERNEL_DTBS
 local -a KEEP_FIRMWARE KERNEL_DISABLE KERNEL_ENABLE
 local REMOVE_MAN_PAGES REMOVE_DOCUMENTATION REMOVE_APT_LISTS PRUNE_KERNEL_DTBS PRUNE_FIRMWARE
 source "${SRC}/config/cleanup/napi-c.conf"
 if [[ $REMOVE_APT_LISTS == yes ]]; then
  run_host_command_logged python3 "${SRC}/tools/clean-napi-files.py" "${SDCARD}" --apply apt
 fi
}
