#!/bin/zsh

set -euo pipefail

if [[ -n "${ZSH_VERSION:-}" ]]; then
  XCODE_ENV_SOURCE_PATH="${(%):-%x}"
elif [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  XCODE_ENV_SOURCE_PATH="${BASH_SOURCE[0]}"
else
  XCODE_ENV_SOURCE_PATH="$0"
fi

ROOT_DIR="$(cd "$(dirname "${XCODE_ENV_SOURCE_PATH}")/../.." && pwd)"
source "${ROOT_DIR}/scripts/lib/product-identity.sh"

PROJECT_PATH="${ROOT_DIR}/${APP_PROJECT_DIR_NAME}/${APP_PROJECT_FILE_NAME}"
SCHEME_NAME="${APP_SCHEME_NAME}"
BUNDLE_IDENTIFIER="${APP_BUNDLE_IDENTIFIER}"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
XCODEBUILD_DIR="${ARTIFACTS_DIR}/xcodebuild"
TEST_RESULTS_DIR="${ARTIFACTS_DIR}/test-results"
CHECKPOINTS_DIR="${ARTIFACTS_DIR}/checkpoints"
DERIVED_DATA_DIR="${ARTIFACTS_DIR}/DerivedData"
FIXTURE_ROOT="${ROOT_DIR}/Fixtures/docs"
EXPECTED_ROOT="${ROOT_DIR}/Fixtures/expected"

MAC_DESTINATION="platform=macOS,arch=arm64"

load_repo_env() {
  local env_path="${ROOT_DIR}/.env"
  [[ -f "${env_path}" ]] || return 0

  local record key value
  while IFS= read -r -d '' record; do
    key="${record%%=*}"
    value="${record#*=}"
    export "${key}=${value}"
  done < <(
    python3 - "${env_path}" <<'PY'
import os
import re
import shlex
import sys

env_path = sys.argv[1]
name_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

with open(env_path, encoding="utf-8") as handle:
    for line_number, raw_line in enumerate(handle, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].lstrip()
        if "=" not in stripped:
            raise SystemExit(f"{env_path}:{line_number}: expected KEY=VALUE entry")

        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if not name_pattern.match(key):
            raise SystemExit(f"{env_path}:{line_number}: invalid variable name '{key}'")
        if key in os.environ:
            continue

        value = raw_value.strip()
        if value:
            parsed = shlex.split(value, posix=True)
            value = parsed[0] if len(parsed) == 1 else " ".join(parsed)
            value = os.path.expanduser(os.path.expandvars(value))
            if value.startswith("./") or value.startswith("../"):
                value = os.path.abspath(os.path.join(os.path.dirname(env_path), value))
        else:
            value = ""

        sys.stdout.write(f"{key}={value}\0")
PY
  )
}

load_repo_env

ensure_dirs() {
  mkdir -p "${ARTIFACTS_DIR}" "${XCODEBUILD_DIR}" "${TEST_RESULTS_DIR}" "${CHECKPOINTS_DIR}" "${DERIVED_DATA_DIR}"
}

xcode_auth_flags() {
  if [[ -n "${ASC_KEY_PATH:-}" || -n "${ASC_KEY_ID:-}" || -n "${ASC_ISSUER_ID:-}" ]]; then
    if [[ -z "${ASC_KEY_PATH:-}" || -z "${ASC_KEY_ID:-}" || -z "${ASC_ISSUER_ID:-}" ]]; then
      echo "set ASC_KEY_PATH, ASC_KEY_ID, and ASC_ISSUER_ID together before using App Store Connect authentication" >&2
      exit 1
    fi

    printf '%s\n' \
      "-authenticationKeyPath" "${ASC_KEY_PATH}" \
      "-authenticationKeyID" "${ASC_KEY_ID}" \
      "-authenticationKeyIssuerID" "${ASC_ISSUER_ID}"
  fi
}

latest_sim_id() {
  local pattern="$1"
  python3 - "${pattern}" <<'PY'
import json
import re
import subprocess
import sys

preferred = re.compile(sys.argv[1])
payload = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "-j", "devices", "available"], text=True))
device_id = None

for runtime in sorted(payload.get("devices", {}).keys()):
    for device in payload["devices"][runtime]:
        if not device.get("isAvailable"):
            continue
        if preferred.search(device.get("name", "")):
            device_id = device.get("udid")

if device_id:
    print(device_id)
PY
}

preferred_sim_id() {
  python3 - "$@" <<'PY'
import json
import subprocess
import sys

preferred_names = sys.argv[1:]
payload = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "-j", "devices", "available"], text=True))
devices_by_runtime = payload.get("devices", {})

for runtime in sorted(devices_by_runtime.keys(), reverse=True):
    devices = [device for device in devices_by_runtime[runtime] if device.get("isAvailable")]
    names_to_ids = {device.get("name"): device.get("udid") for device in devices}
    for name in preferred_names:
        if name in names_to_ids:
            print(names_to_ids[name])
            raise SystemExit(0)
raise SystemExit(1)
PY
}

iphone_sim_id() {
  local id
  id="$(preferred_sim_id \
    "iPhone 17" \
    "iPhone 17 Pro" \
    "iPhone 16e" \
    "iPhone Air" \
    "iPhone 16" \
    "iPhone 15 Pro" \
    "iPhone 15" \
    "iPhone SE (3rd generation)")"
  if [[ -z "${id}" ]]; then
    return 1
  fi
  printf '%s\n' "${id}"
}

ipad_sim_id() {
  local id
  id="$(preferred_sim_id \
    "iPad Air 11-inch (M3)" \
    "iPad Pro 11-inch (M5)" \
    "iPad mini (A17 Pro)" \
    "iPad (A16)" \
    "iPad Pro 11-inch (M4)" \
    "iPad Pro (11-inch) (4th generation)" \
    "iPad Air 11-inch (M2)" \
    "iPad (10th generation)")"
  if [[ -z "${id}" ]]; then
    return 1
  fi
  printf '%s\n' "${id}"
}

result_bundle_path() {
  local name="$1"
  printf '%s/%s.xcresult\n' "${XCODEBUILD_DIR}" "${name}"
}

app_bundle_path() {
  printf '%s/Build/Products/Debug/%s.app\n' "${DERIVED_DATA_DIR}" "${APP_PRODUCT_NAME}"
}

ios_app_bundle_path() {
  printf '%s/Build/Products/Debug-iphonesimulator/%s.app\n' "${DERIVED_DATA_DIR}" "${APP_PRODUCT_NAME}"
}

app_binary_path() {
  printf '%s/Contents/MacOS/%s\n' "$(app_bundle_path)" "${APP_PRODUCT_NAME}"
}

ios_platform_installed() {
  xcodebuild -showdestinations -project "${PROJECT_PATH}" -scheme "${SCHEME_NAME}" 2>/dev/null | grep -q "platform:iOS Simulator"
}

require_project() {
  [[ -d "${PROJECT_PATH}" ]] || {
    echo "Missing project at ${PROJECT_PATH}" >&2
    exit 1
  }
}
