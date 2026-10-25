# Pepecoin ElectrumX

```text
Licence: MIT
Original Author: Neil Booth
Current Maintainers: The Electrum developers
Language: Python (>= 3.10)
```

The attribution above describes upstream ElectrumX. Pepecoin adaptations and this
repository's maintenance are documented in [provenance](docs/PROVENANCE.md).

Standalone, source-built Pepecoin ElectrumX 1.18.0 with an optional PHP dashboard.
This repository starts with fresh history; it contains no Pepecoin Service website,
faucet, donation service, Discord credentials, live databases, or production configs.

## Status and scope

This is a maintained reconstruction, not an official Pepecoin Core release and not
a drop-in replacement for the legacy combined Apache/ElectrumX container. Read
[provenance](docs/PROVENANCE.md) and [migration](docs/MIGRATION.md) before switching.
Registry publishing is gated and initially release-candidate only; no stable image
has been certified. Use a reviewed source commit or actual published candidate
digest, not the historical baseline import commit or an example placeholder.

A versioned daemon candidate pipeline is provided; see
[container releases and upgrades](docs/CONTAINER-RELEASES.md) and the
[current security review](docs/RELEASE-SECURITY.md). Candidate status is not a
stable-release certification. The optional dashboard is not published while its
remaining Critical package findings are under review.

The first [published daemon candidate, v1.18.0-pep.1-rc.1](docs/releases/v1.18.0-pep.1-rc.1.md),
is available anonymously from GHCR. Read its exact digest, verification status,
and limitations before opting in; a candidate is not a stable-release endorsement.

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

## Optional private dashboard

Create `secrets/dashboard_password` containing a unique, strong password (at least
20 characters). Do not commit the file. Restrict the directory to its owner, and
ensure the mounted file is readable by the container's Apache user. Compose local
file secrets are bind mounts; do not assume its `uid`/`mode` fields change host-file
permissions. With a 0700 parent directory, a readable file inside it can be mounted
without granting other host users traversal access.

```sh
docker compose --profile dashboard build --pull --no-cache dashboard
docker compose --profile dashboard up -d dashboard
```

Connect to `http://127.0.0.1:8002` on the host, or use an SSH local port forward.
Do not expose this legacy administrative dashboard publicly. Its application
controls can affect Electrum sessions. Authentication does not make it a hardened
public web application. Geolocation lookups are disabled by default.

The `dashboard_data` named volume stores runtime state separately from the image.
Its `.htaccess` denies HTTP access. Back up both named volumes and your local
configuration before upgrades. Never run `docker compose down -v` on a live index.

## Change review

The baseline import, deployed history-compaction safeguards, PHP/Brotli updates,
dashboard authentication hardening, and optional legacy-image compatibility patch are kept in
separate commits. Review the relevant commit instead of merging unrelated changes.
See [separate security diffs](docs/CHANGE-REVIEW.md) and
[verification results and reproducible checks](docs/VERIFICATION.md).

If you only need the reported Brotli fix while retaining the original combined
container, use [the standalone compatibility patch](patches/emgi-brotli/README.md), not this
repository's root Compose deployment.

## Licenses

ElectrumX is MIT-licensed; retain `LICENSE` and `electrumx/LICENCE`. The dashboard
has its own MIT notice in `dashboard/LICENSE`. See provenance for upstream and
Pepecoin contributor attribution. Existing notices are retained, not replaced.
