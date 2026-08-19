#!/bin/zsh

set -euo pipefail
unsetopt BG_NICE

readonly REPOSITORY_DIR="${0:A:h}"
readonly NODE_VERSION="24.19.0"
readonly TOOLS_DIR="$REPOSITORY_DIR/.site-tools"

case "$(uname -m)" in
  arm64) readonly NODE_ARCH="arm64" ;;
  x86_64) readonly NODE_ARCH="x64" ;;
  *) readonly NODE_ARCH="unsupported" ;;
esac

readonly NODE_FOLDER="$TOOLS_DIR/node-v$NODE_VERSION-darwin-$NODE_ARCH"

cd "$REPOSITORY_DIR"

show_error() {
  /usr/bin/osascript - "$1" <<'APPLESCRIPT' >/dev/null
on run argv
  display dialog (item 1 of argv) with title "Website Preview" buttons {"OK"} default button "OK" with icon stop
end run
APPLESCRIPT
}

node_is_compatible() {
  [[ -x "$1" ]] && [[ "$("$1" --version 2>/dev/null)" == "v$NODE_VERSION" ]]
}

find_node() {
  if [[ -n "${SITE_PREVIEW_NODE:-}" ]] && node_is_compatible "$SITE_PREVIEW_NODE"; then
    print -r -- "$SITE_PREVIEW_NODE"
    return
  fi

  if (( $+commands[node] )) && node_is_compatible "${commands[node]}"; then
    print -r -- "${commands[node]}"
    return
  fi

  if node_is_compatible "$NODE_FOLDER/bin/node"; then
    print -r -- "$NODE_FOLDER/bin/node"
    return
  fi

  return 1
}

install_node() {
  local architecture archive_name archive_path checksum download_url response
  architecture="$(uname -m)"

  case "$architecture" in
    arm64)
      archive_name="node-v$NODE_VERSION-darwin-arm64.tar.gz"
      checksum="8294b7aa9b03997481c06babf1e8b270c859358f27da57a11509afe537ac381d"
      ;;
    x86_64)
      archive_name="node-v$NODE_VERSION-darwin-x64.tar.gz"
      checksum="d1b5e999db158c62fe8f7267a4476b035d8bd93b1a605bac24a3f0dd166e3316"
      ;;
    *)
      show_error "This launcher supports Apple Silicon and Intel Macs."
      exit 1
      ;;
  esac

  response=$(/usr/bin/osascript <<'APPLESCRIPT'
display dialog "The first preview needs a private copy of Node.js and the website dependencies. They will be downloaded into this website folder and will not change the rest of your Mac." with title "Set up Website Preview" buttons {"Cancel", "Download and Continue"} default button "Download and Continue" cancel button "Cancel"
return button returned of result
APPLESCRIPT
  ) || exit 0

  [[ "$response" == "Download and Continue" ]] || exit 0

  /bin/mkdir -p "$TOOLS_DIR"
  archive_path="$TOOLS_DIR/$archive_name"
  download_url="https://nodejs.org/dist/v$NODE_VERSION/$archive_name"

  print "Downloading the preview runtime from nodejs.org..."
  /usr/bin/curl --fail --location --progress-bar "$download_url" --output "$archive_path"

  if [[ "$(/usr/bin/shasum -a 256 "$archive_path" | /usr/bin/awk '{print $1}')" != "$checksum" ]]; then
    show_error "The downloaded Node.js file did not pass its security check. Nothing was installed."
    exit 1
  fi

  /usr/bin/tar -xzf "$archive_path" -C "$TOOLS_DIR"
  /bin/rm -f -- "$archive_path"
}

NODE_BIN="$(find_node || true)"
if [[ -z "$NODE_BIN" ]]; then
  install_node
  NODE_BIN="$(find_node || true)"
fi

if [[ -z "$NODE_BIN" ]]; then
  show_error "Node.js $NODE_VERSION could not be prepared."
  exit 1
fi

NODE_BIN_DIR="${NODE_BIN:h}"
export PATH="$NODE_BIN_DIR:$PATH"
NPM_BIN="$NODE_BIN_DIR/npm"

install_dependencies() {
  if [[ -n "${SITE_PREVIEW_PNPM:-}" ]]; then
    "$SITE_PREVIEW_PNPM" install --frozen-lockfile
  else
    "$NPM_BIN" exec --yes pnpm@11.19.0 -- install --frozen-lockfile
  fi
}

if [[ ! -x "$NPM_BIN" ]]; then
  show_error "The preview runtime is missing npm."
  exit 1
fi

if [[ ! -x "$REPOSITORY_DIR/node_modules/.bin/astro" ]]; then
  print "Installing the website dependencies (first preview only)..."
  install_dependencies
fi

print "Checking and building the website..."
export ASTRO_TELEMETRY_DISABLED=1

# Astro loads these files itself. Use the documented public demo identifier
# only when the user has not configured one, so a fresh double-click preview
# still produces the complete site and passes the production-style checks.
fastcomments_is_configured=0
if [[ -n "${PUBLIC_FASTCOMMENTS_TENANT_ID:-}" ]]; then
  fastcomments_is_configured=1
else
  for env_file in .env .env.local .env.production .env.production.local; do
    if [[ -f "$env_file" ]] && /usr/bin/grep -Eq '^[[:space:]]*PUBLIC_FASTCOMMENTS_TENANT_ID[[:space:]]*=[[:space:]]*[^[:space:]#]+' "$env_file"; then
      fastcomments_is_configured=1
      break
    fi
  done
fi
if (( ! fastcomments_is_configured )); then
  export PUBLIC_FASTCOMMENTS_TENANT_ID=demo
fi

# npm is already bundled with the private Node runtime. `npm run` executes the
# installed local tools without resolving pnpm over the network on every run.
"$NPM_BIN" run build
if (( $+commands[python3] )); then
  "$NPM_BIN" run validate
else
  print "The optional extended link checks need Python; GitHub will run them before publishing."
fi

if [[ "${SITE_PREVIEW_CHECK_ONLY:-0}" == "1" ]]; then
  print "Preview checks passed."
  exit 0
fi

port=4321
while /usr/bin/nc -z 127.0.0.1 "$port" >/dev/null 2>&1; do
  (( port += 1 ))
done

preview_url="http://127.0.0.1:$port/"
print "Opening $preview_url"
"$NODE_BIN" "$REPOSITORY_DIR/scripts/serve-preview.mjs" "$port" &
preview_pid=$!
trap '/bin/kill "$preview_pid" >/dev/null 2>&1 || true' EXIT HUP INT TERM

for _ in {1..80}; do
  if /usr/bin/curl --fail --silent "$preview_url" >/dev/null 2>&1; then
    if [[ "${SITE_PREVIEW_NO_OPEN:-0}" != "1" ]]; then
      /usr/bin/open "$preview_url"
    fi
    print "Preview opened. Close this window when you are finished."
    wait "$preview_pid"
    exit $?
  fi
  /bin/sleep 0.25
done

show_error "The website built successfully, but the preview server did not start."
exit 1
