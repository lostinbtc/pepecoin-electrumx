# Pepecoin ElectrumX

```text
Licence: MIT
Original Author: Neil Booth
Current Maintainers: The Electrum developers
Language: Python (>= 3.10)
```

Standalone Pepecoin ElectrumX 1.18.0 with Docker images and an optional patched dashboard.

## Status and scope

The Docker images are Linux/amd64 release candidates. The
[ElectrumX image](docs/releases/v1.18.0-pep.1-rc.1.md) has passed full-chain indexing
and restart/protocol checks. Release notes include verified digests, test results
and known limitations.

See [setup and upgrades](docs/CONTAINER-RELEASES.md),
[security findings](docs/RELEASE-SECURITY.md), and
[dashboard setup and its security patch](docs/DASHBOARD.md).
If switching from a combined ElectrumX/dashboard container, follow the
[migration guide](docs/MIGRATION.md); this uses separate services.

The Electrum daemon and dashboard are separate services. The dashboard is disabled
unless the `dashboard` Compose profile is selected. Only Electrum ports 50001,
50002, and 50004 are public. Administrative RPC 8000 is internal to Docker.

## Configure and build

Requirements: Docker Engine with Compose v2, a synced Pepecoin Core node with
transaction indexing enabled, valid TLS certificates, and sufficient persistent
storage for a fresh ElectrumX index. Use Linux/amd64 for the initially tested build;
other architectures require independent validation.

1. Copy `.env.example` to `.env` and replace the example values.
2. Create `certs/` and put your full certificate chain and private key there,
   matching the filenames in `.env`. Keep the private key restricted to its owner.
3. Configure Core RPC so this Docker network can reach it. The supplied host-gateway
   mapping does not open a firewall or change Core's RPC bind/allowlist. Never expose
   Core RPC publicly. Use your own credentials; URL-encode reserved characters.
4. Build and start the daemon:

```sh
docker compose build --pull --no-cache electrumx
docker compose up -d electrumx
docker compose logs --tail 100 electrumx
docker compose exec -T electrumx electrumx_rpc getinfo
```

A fresh index may take considerable time. The database and daemon heights should
converge. Do not treat an open socket alone as proof of synchronization.

## Optional patched dashboard

**Wallets and direct Electrum RPC clients do not need the dashboard.** Add it only
for its web interface or a tool that specifically depends on its HTTP endpoints.
See [the dashboard security patch and deployment instructions](docs/DASHBOARD.md).
The [optional dashboard image v1.0.0-rc.1](docs/releases/dashboard-v1.0.0-rc.1.md)
is available anonymously, with its verified digest and scan results recorded.

The dashboard includes **PHP 8.4.27 and Apache**. Its runtime packages were updated
and security-scanned on **October 25, 2026**, with zero reported package
vulnerabilities in the published image at that time. Future security fixes require
an updated image; this is not an automatic-update guarantee.

Create `secrets/dashboard_password` containing a unique, strong password (at least
20 characters). Do not commit the file. Restrict the directory to its owner, and
ensure the mounted file is readable by the container's Apache user. Compose local
file secrets are bind mounts; do not assume its `uid`/`mode` fields change host-file
permissions. With a 0700 parent directory, a readable file inside it can be mounted
without granting other host users traversal access.

```sh
docker compose --profile dashboard build --pull --no-cache dashboard
docker compose --profile dashboard up -d --no-deps dashboard
```

Connect to `http://127.0.0.1:8002` on the host, or use an SSH local port forward.
Keep this administrative dashboard private: its controls can affect Electrum
sessions. Geolocation lookups are disabled by default.

The `dashboard_data` named volume stores runtime state separately from the image.
Apache denies direct HTTP access to that data. Back up both named volumes and your local
configuration before upgrades. Never run `docker compose down -v` on a live index.

## Change review

See [security patches](docs/CHANGE-REVIEW.md) and
[verification results and reproducible checks](docs/VERIFICATION.md).

If you only need the reported Brotli fix while retaining the original combined
container, use [the standalone compatibility patch](patches/emgi-brotli/README.md), not this
repository's root Compose deployment.

## Licenses

ElectrumX is MIT-licensed; retain `LICENSE` and `electrumx/LICENCE`. The dashboard
has its own MIT notice in `dashboard/LICENSE`. Retain the author and copyright
notices supplied with each component.
