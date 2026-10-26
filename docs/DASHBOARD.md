# Optional ElectrumX dashboard

**You probably do not need this for wallets or direct Electrum RPC monitoring.**
ElectrumX runs independently. Add this separate container only if you want its
private web interface, or an existing integration specifically reads dashboard
HTTP endpoints. The third-party Discord bot's integration remains unverified.
Installing the dashboard is not required to use the standalone daemon or apply
the [original-image Brotli-only patch](../patches/emgi-brotli/README.md).

The [published v1.0.0-rc.1 dashboard candidate](releases/dashboard-v1.0.0-rc.1.md)
includes its exact digest, anonymous download, scan summary and verification results.

## Exact security patch

- [Review the dashboard security patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/d02676e5e4f257419247ded31a538306bdd29793).
- [Download that exact patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/d02676e5e4f257419247ded31a538306bdd29793.patch).

This patch applies to this repository's **split dashboard**, not blindly to a
legacy combined image. It replaces the Debian/PHP 8.2 packaging with pinned Alpine
3.24.3 and distribution-maintained Apache/PHP 8.4 packages, with minimum security
revisions. It preserves the data path and UID/GID 33, runtime password-file and
RPC environment variables, and HTTP port 80. Electrum protocol and database code
are unchanged. Apache now denies direct source, view, data and dotfile access;
query-string tokens are omitted from access logs. Compose uses a read-only root
filesystem, no-new-privileges, temporary session/PID directories and separate data.

The local 2026-10-25 image scan found **zero reported package vulnerabilities and
zero secrets**. Tests passed for missing/wrong passwords, spoofed localhost Host,
login, empty and populated pages, protected paths, UID-33 data writes and persisted
data after restart. This is not a complete application security audit or a promise
that future scans will be clean. See [security findings](RELEASE-SECURITY.md).

## Private setup

Configure the daemon as in the main README. Create an operator-owned
`secrets/dashboard_password` containing at least 20 random characters; never commit
it. Keep its parent directory restricted and allow UID 33 to read the mounted
file. File secrets are bind mounts: Compose does not rewrite their host ownership.

For source builds:

```sh
docker compose --profile dashboard build --pull --no-cache dashboard
docker compose --profile dashboard up -d --no-deps dashboard
```

For a published candidate, set `DASHBOARD_IMAGE` in your private `.env` to the
reviewed full registry-digest reference in its release notes, then:

```sh
docker compose --profile dashboard pull dashboard
docker compose --profile dashboard up -d --no-build --no-deps dashboard
docker compose --profile dashboard logs --tail 100 dashboard
```

The daemon must already be running in the same Compose project. `--no-deps`
prevents a dashboard update from recreating it. Use `http://127.0.0.1:8002` locally
or an SSH tunnel. **Do not expose this administrative application publicly.** Its
controls can affect Electrum sessions. Geolocation requests remain disabled.

Before updating, record the old dashboard digest and stop only the dashboard to
back up `dashboard_data` consistently. Preserve your password file and `.env`.
Keep an untouched backup for rollback; never delete the daemon's database or use
`docker compose down -v`. Ordinary PHP sessions in `/tmp` expire on restart; sign
in again. Custom Apache/PHP configs need review because the base layout changed.

## Maintenance and scope

The dashboard has its own candidate tags, scan gate, SBOM and publishing workflow.
It is Linux/amd64-only until other architectures are independently verified; no
`latest` or stable tag is automatically published. Publication blocks every Critical
finding, fixable High findings and detected secrets, without an ignore list.

Alpine's `community` repository is supported only until the next stable release,
unlike the longer `main` support period. PHP is a community package: review and
upgrade the base branch at the next Alpine stable release, then rebuild, scan and
retest. A pinned digest prevents surprise updates; it does not install future fixes
automatically. See [Alpine's support policy](https://alpinelinux.org/releases/) and
[PHP's supported branches](https://www.php.net/supported-versions.php).
