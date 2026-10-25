#!/usr/bin/env bash

set -Eeuo pipefail

# Make sure required environment variables are set
if [ -z "${SSL_CERTFILE:-}" ] || [ -z "${SSL_KEYFILE:-}" ]; then
  echo "Error: SSL_CERTFILE and/or SSL_KEYFILE environment variables are not set."
  exit 1
fi

if [ -z "${DB_DIRECTORY:-}" ]; then
  echo "Error: DB_DIRECTORY environment variable is not set."
  exit 1
fi

# Create the directory if it doesn't exist (optional/safe)
mkdir -p "$(dirname "$SSL_CERTFILE")"
mkdir -p "$DB_DIRECTORY"

# Check if cert and key files exist
if [ ! -f "$SSL_CERTFILE" ] || [ ! -f "$SSL_KEYFILE" ]; then
  echo "Error: SSL certificate or key files do not exist."
  echo "CERT: $SSL_CERTFILE"
  echo "KEY:  $SSL_KEYFILE"
  exit 1
fi

# Set strict permissions when the mount allows it.
# Read-only cert mounts are fine as long as the files already exist.
if [ -w "$SSL_CERTFILE" ] && [ -w "$SSL_KEYFILE" ]; then
  chmod 600 "$SSL_CERTFILE" "$SSL_KEYFILE"
else
  echo "Cert files are read-only; skipping chmod."
fi

# The legacy history format has a two-byte flush ID.  Compact well before it
# reaches 65,535, and finish any compaction interrupted by a prior shutdown.
set +e
/usr/local/bin/electrumx_history_compaction_guard
guard_status=$?
set -e

case "$guard_status" in
  0)
    ;;
  75)
    echo "ElectrumX history requires offline compaction before startup."
    /usr/local/bin/electrumx_compact_history

    # The old compactor historically swallowed failures.  Verify the database
    # independently even though it now also returns a proper failure status.
    set +e
    /usr/local/bin/electrumx_history_compaction_guard
    guard_status=$?
    set -e
    if [ "$guard_status" -ne 0 ]; then
      echo "Error: history still requires compaction; refusing unsafe startup."
      exit 1
    fi
    ;;
  *)
    echo "Error: history compaction guard could not validate the database."
    exit "$guard_status"
    ;;
esac

# Replace the shell so Docker's stop signal reaches ElectrumX directly.
exec /usr/local/bin/electrumx_server
