# Optional dashboard v1.0.0-rc.1 — Linux/amd64

**Optional:** wallets and direct Electrum RPC clients do not need this dashboard.
Use it only for the private web interface or dashboard-dependent integrations.
This is a separate release candidate, not a replacement for the daemon image.

## Download and exact artifact

[Container package](https://github.com/lostinbtc/pepecoin-electrumx/pkgs/container/pepecoin-electrumx-dashboard)

```sh
docker pull ghcr.io/lostinbtc/pepecoin-electrumx-dashboard:v1.0.0-rc.1
```

Pin deployments to the verified registry digest:

```text
DASHBOARD_IMAGE=ghcr.io/lostinbtc/pepecoin-electrumx-dashboard@sha256:43592f912a5af7017762229c21829566e9493a74dbc0cef12060a490a7f81639
```

Source revision: `c2e28c1c1964f9729bf9da9aee38dc4730b1c5e0`.
Local image/config ID: `sha256:d86b3eede2db68878706f909a244008a8645bac29fd878be6fc81b6917b73577`.
The config ID is not the registry digest used for pulling.

## Security patch citation

[Review the exact security patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/d02676e5e4f257419247ded31a538306bdd29793)
or [download it as a patch file](https://github.com/lostinbtc/pepecoin-electrumx/commit/d02676e5e4f257419247ded31a538306bdd29793.patch).
The independent publication workflow was added separately in
[49c9bb7](https://github.com/lostinbtc/pepecoin-electrumx/commit/49c9bb7).

The patched image uses Alpine 3.24.3, Apache 2.4.69, PHP 8.4.27, Brotli 1.2.1,
libxml2 2.13.9-r2 and zlib 1.3.2-r1. SQLite is not installed. See
[scope, migration and maintenance](../DASHBOARD.md) and
[the historical package findings](../RELEASE-SECURITY.md).

## Verification

[Successful build/test/scan/publication](https://github.com/lostinbtc/pepecoin-electrumx/actions/runs/40257235097).
CI publishes the same tested image, with an SBOM and verification artifacts.
Anonymous manifest retrieval (HTTP 200) and a pull with an empty Docker credential
configuration succeeded. The downloaded registry image was independently retested
and rescanned on 2026-10-25 (America/Phoenix):

- Missing password and spoofed localhost Host fail closed; wrong password rejected.
- Login and repeated authenticated requests work.
- Empty and synthetic populated session/peer pages render without PHP errors.
- Data, source, views and dotfiles cannot be fetched over HTTP.
- Read-only root filesystem, UID-33 data writes and clean restart/data persistence pass.
- Trivy 0.76.1 scanned 43 packages: **zero reported vulnerabilities and zero secrets**.
  No scanner exclusions were used. [Sanitized scan summary](dashboard-v1.0.0-rc.1-scan.json).

This is package-level and targeted integration verification, not a complete web
application security audit. Keep the dashboard bound to loopback or use an SSH
tunnel. The third-party Discord bot was not supplied and remains unverified.
Only Linux/amd64 was tested; no stable/latest tag is being promoted. Future Alpine
branch/package updates require new scans and tests. The daemon image and production
services were not changed by this release.
