# Standalone Brotli fix for the original emgi image

You do **not** need to adopt this repository's split deployment, history guard,
dashboard authentication changes, or Compose file to use this patch.

This Dockerfile derives from the exact supplied emgi digest and updates only the
Debian Brotli package (and any dependencies APT requires). It retains the combined
Apache/ElectrumX entrypoint, application code, environment defaults, declared ports,
and database paths. There are no `COPY` instructions and no operator secrets.

The inspected Linux/amd64 base uses Debian 13 and has `libbrotli1 1.1.0-2+b7`.
The build requires trixie and rejects any installed revision older than the fixed
`1.1.0-2+deb13u1`. Debian backports the fix; the upstream version string can remain
`1.1.0`. Reference: <https://security-tracker.debian.org/tracker/CVE-2026-111497>.

## Build and inspect without starting the server

From the repository root:

```sh
docker build --pull --no-cache \
  -t pepecoin-electrum:emgi-brotli-fixed patches/emgi-brotli
docker run --rm --network none --entrypoint dpkg-query \
  pepecoin-electrum:emgi-brotli-fixed -W libbrotli1
```

This is a local image name, not a published registry tag or pullable digest. If you
publish your rebuilt image, record the registry digest returned by that registry.
Do not substitute the local Docker image/config ID for a registry manifest digest.

## Deploy using your existing configuration

1. Save your original image digest and privately back up configuration/certificates.
2. Stop ElectrumX cleanly and make a consistent backup of its database and dashboard
   runtime data. Never test two processes against the same database.
3. In **your existing** Compose definition or deployment configuration, change only
   the image reference to your rebuilt image. Preserve your environment, mounts,
   ports, and container/service names. Do not use this repository's root Compose
   file for this compatibility patch.
4. Recreate the relevant container; `docker restart` alone does not select a new
   image. The inherited entrypoint performs its original unconditional compaction.
   Allow for that behavior and verify its result before relying on the server.
5. Check protocol negotiation, chain identity and height on TCP/TLS/WSS, dashboard
   login, local administrative RPC if used, and your bot's actual read-only checks.

Keep the prior image and untouched backup for rollback. Rolling back restores the
affected Brotli package, so it is an emergency recovery option, not the final fix.

## Limits

This patch updates Brotli in the exact pinned emgi image while preserving its
application code and deployment configuration. It was verified on Linux/amd64;
other architectures require testing. Whether the affected decoder was reachable
in your deployment remains unconfirmed.
