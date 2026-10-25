# Standalone container releases

The maintained daemon is built from `electrumx/`, not from the legacy image. The
optional dashboard is separate. This is not a drop-in replacement for a combined
Apache/ElectrumX deployment; read [migration](MIGRATION.md) first.

## Candidate pipeline

`.github/workflows/container-candidate.yml` runs on main, pull requests, and
explicit candidate tags such as `v1.18.0-pep.1-rc.1`. Main/PR runs do not publish.
The pipeline:

1. Checks Git history for secrets with a checksum-pinned scanner.
2. Builds Linux/amd64 images, linking the daemon to its source commit via OCI labels.
3. Runs upstream/history-guard/release-policy tests in a disposable test container.
4. Exercises the exact runtime image against the real genesis fixture, including
   verified TLS/WSS, local administrative RPC, and a persisted-database restart.
5. Checks dashboard authentication and empty-state behavior separately.
6. Scans runtime images and produces a daemon SBOM and sanitized scan summaries.
7. On a candidate tag only, transfers the **same tested daemon image** to a separate
   publishing job and pushes it to `ghcr.io/lostinbtc/pepecoin-electrumx:<tag>`.

Publishing uses the repository's short-lived `GITHUB_TOKEN` with `packages: write`
only in the publishing job. It does not require an operator's Core RPC credentials,
Discord token, SSH key, or database. No `latest` or stable tag is published by this
workflow. The dashboard is tested/scanned but is **not published** by it.

The gate blocks detected secrets, every Critical finding, and High findings with
an available fix. Unfixed High findings are explicitly disclosed, not hidden with
an ignore list. Passing this candidate gate is not proof of exploit absence or a
full security audit. See [security review](RELEASE-SECURITY.md).

GitHub initially makes a new container package private. The owner must make the
package public once in its GitHub package settings, then verify an anonymous pull.
A public source repository does not by itself prove its container is public.
See [GitHub's Container Registry documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## Before calling a candidate stable

- Download the candidate by its actual registry digest. Inspect its source label.
- Finish a fresh full-chain index, verify that its height/hash matches Core, and
  verify transaction proofs, verified TLS/WSS, and recovery after a clean restart.
- Record the image ID **and registry digest** in the verification evidence. A local
  build's success is not automatically proof of an independently rebuilt CI image.
- Review unresolved scanner findings and update the scan immediately before release.
- Confirm the operator's real monitoring integration, or explicitly state that it
  remains unverified. The community member's Discord bot has not been supplied.
- Prepare migration/rollback instructions and release notes. Promote deliberately;
  do not overwrite an already published version tag with a different image.

The CI genesis test is not a full-chain test. Full-chain verification needs an
operator-provided read-only Core bridge; production credentials are not put into CI.
No workflow automatically promotes a candidate to stable.

## Operator setup using a published daemon image

Clone this repository for configuration and documentation, copy `.env.example` to
`.env`, and set your Core RPC URL, hostname and certificate paths as in the README.
Set `ELECTRUM_IMAGE` in `.env` to the **real digest copied from a reviewed release**:

```text
ELECTRUM_IMAGE=ghcr.io/lostinbtc/pepecoin-electrumx@sha256:REPLACE_WITH_REAL_RELEASE_DIGEST
```

The placeholder above is not a usable image. Use a release-candidate tag only if
you deliberately accept its documented limitations. Confirm package visibility
before announcing that anonymous users can pull it.

```sh
docker compose pull electrumx
docker compose up -d --no-build electrumx
docker compose logs --tail 100 electrumx
docker compose exec -T electrumx electrumx_rpc getinfo
```

The `build:` section remains available for source users; `--no-build` ensures that
the prebuilt-image path does not silently compile a different image. Do not run
`docker compose build` with an upstream registry reference configured: that would
locally retag a source build under the configured name.

The daemon uses a read-only root filesystem and disables new privileges. It drops
all capabilities except `DAC_OVERRIDE`, needed to read restrictive operator-owned
certificate files through read-only mounts without weakening their host permissions.
Its database remains writable in the separate `/data` volume.
Only TCP/TLS/WSS are published; administrative RPC remains internal. Keep the
dashboard private and source-built until it has a separately reviewed release.

## Future upgrades and rollback

Pull the next reviewed digest while the old service runs. Before cutover, stop
ElectrumX cleanly and take a consistent backup of its database and any dashboard
runtime data. Privately preserve `.env`, certificates and secret files, and record
the old digest. Recreate the service with the new image, then verify synchronization
and actual client/monitoring behavior. `docker restart` does not select a new image.

Normal upgrades reuse persistent storage. A release that changes database formats
must have explicit migration instructions. Never run two writers against one
database, never run `docker compose down -v` on a live index, and never assume a
database modified by a newer release can be opened safely by an older one. For
rollback, use the prior image and the untouched matching backup.

### Long-running history maintenance

The legacy history format uses a 16-bit flush identifier. The included guard checks
it **at startup**, with a default `HISTORY_COMPACTION_THRESHOLD=50000`; it is not a
continuous maintenance scheduler. Watch `db_flush_count` in `electrumx_rpc getinfo`
and arrange a clean restart when it reaches your configured threshold, before the
65,536 boundary. Startup then performs any required offline compaction and verifies
its result before serving. Allow for that maintenance downtime. Do not run the
offline guard or compactor against a database already open by the running daemon,
and do not rely on an overflow-triggered crash/restart as the maintenance plan.

## Repeat the local tests

Build the images following the README. The production image deliberately lacks
compilers and pip; install test tooling only in a disposable container, as shown in
the CI workflow. Runtime protocol checks add no packages to the tested image:

```sh
python3 tests/check_electrum.py --image pepecoin-electrumx:local \
  --output /path/to/new/genesis-test-directory
```

For an actual full-chain index, provide a local **read-only, rate-limited** RPC
bridge to an unpruned, synchronized Core node with transaction indexing enabled.
The test refuses a credential-bearing or non-loopback bridge URL:

```sh
export CHAIN_TEST_DAEMON_URL=http://127.0.0.1:YOUR_READ_ONLY_BRIDGE_PORT
python3 tests/check_electrum.py --image YOUR_REVIEWED_IMAGE \
  --full-chain --progress-seconds 120 --output /path/to/new/full-chain-test-directory
```

The test creates its own empty Docker volume and random container, opens only
loopback listeners, disables peer discovery/announcements, and removes its own
container/volume afterward. Reports and logs remain in the output directory.
`--keep-database` retains the explicitly named test volume for investigation.
SIGINT/SIGTERM initiates clean shutdown. It never selects a production database.
This harness uses Linux host networking and requires privileged Docker access.

To resume an interrupted full-chain test that used `--keep-database`, keep its
original reports and provide a **new** output directory:

```sh
python3 tests/check_electrum.py --image YOUR_SAME_REVIEWED_IMAGE \
  --full-chain --keep-database --progress-seconds 120 \
  --resume-run /path/to/previous/full-chain-test-directory \
  --output /path/to/new/resumed-test-directory
```

Resume requires the exact original image ID, a stopped/failed run, verified fresh
test origin, the harness's volume name/ownership label, and no attached container.
It does not accept arbitrary existing databases. Both runs' evidence must be kept:
resuming does not erase earlier errors or turn a partial index into a completed
full-chain test. These checks are operator safeguards, not a security boundary
against someone who can alter Docker resources or test metadata.
