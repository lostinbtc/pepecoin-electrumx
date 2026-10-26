# Standalone release-candidate security review

Local scan date: 2026-10-25. Scanner: Trivy 0.76.1, freshly downloaded vulnerability
database. These are package findings, not evidence that a network attacker can
reach every affected code path. Counts can change as advisory databases change.

## Packaging changes

The daemon now uses a multi-stage build. Compilers and development headers stay
in the builder; the runtime contains the required LevelDB library and application
dependencies. pip and its bundled libraries, setuptools, wheel and packaging are
removed from the runtime because serving Electrum does not require them. Test-only
containers reinstall tooling when needed. Reviewed Python runtime dependencies
are constrained in `electrumx/requirements-runtime.txt`.

Base images are pinned by digest. Debian packages are refreshed at build time;
therefore independent builds are not promised to be bit-for-bit identical.
Release images need their own recorded registry digest and verification evidence.
Build-only artifacts and test certificates are excluded from image contexts.

The optional dashboard now uses pinned Alpine 3.24.3 with maintained Apache 2.4.69
and PHP 8.4.27 packages, Brotli 1.2.1, libxml2 2.13.9-r2 and zlib 1.3.2-r1 minimums.
SQLite is not installed. UID/GID 33 and the data/password/RPC interface are retained.
There are no Electrum application-code or database-format changes. Review the
[exact optional dashboard patch](https://github.com/lostinbtc/pepecoin-electrumx/commit/d02676e5e4f257419247ded31a538306bdd29793.patch)
and [maintenance requirements](DASHBOARD.md).

## Local results

| Runtime image | Critical | High | High with available fix | Secret findings |
| --- | ---: | ---: | ---: | ---: |
| Daemon candidate | 0 | 44 | 0 | 0 |
| Optional Alpine dashboard candidate | 0 | 0 | 0 | 0 |

The updated dashboard scan reported zero findings at all severities across 43
installed packages. Its prior Debian-based candidate had 3 Critical and 109 High
package matches and was held from publication. Scan databases change over time;
zero current findings is not an application security certification.
The [published dashboard candidate](releases/dashboard-v1.0.0-rc.1.md) was also
anonymously pulled, retested and rescanned by exact registry digest; its recorded
summary has the same zero-finding result.

Counts are package/advisory matches, not necessarily distinct vulnerabilities.
The daemon's 44 High matches represent these eight distinct advisories:

- CVE-2025-69720 (ncurses)
- CVE-2026-16742 (systemd)
- CVE-2026-54369 (acl)
- CVE-2026-76642 (util-linux)
- CVE-2026-78408 (util-linux)
- CVE-2026-78409 (util-linux)
- CVE-2026-78410 (util-linux)
- CVE-2026-9538 (Perl)

The scanner reports no available fixed package revision for those matches in this
Debian base at scan time. This does not establish that they are harmless. Compose
also drops daemon capabilities except `DAC_OVERRIDE` (for reading restrictive
operator-owned certificate mounts) and sets `no-new-privileges`; these are defense
in depth, not a substitute for upstream fixes. Keep tracking Debian advisories and
rebuilding/retesting when fixes become available. No global ignore list was added.

### Component-level context for the published daemon candidate

Read-only inspection of registry digest
`sha256:1449b990ad0d37afb79e8a72be0781427235f67de7acc773a50adba38b51089d`
found the following. This records evidence without suppressing scanner results:

| Advisory/component | Observed context |
| --- | --- |
| [CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742), systemd-homed | Debian describes a local privilege issue in homed-managed accounts. The homed executable was absent from its standard paths; the image contains a systemd-family library package, not a running homed service. |
| [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538), Perl Archive::Tar | Debian describes tar-entry memory exhaustion in that module. Loading the module failed, and no `Tar.pm` was present in the standard installed Perl module directories checked. |
| [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720), infocmp | The affected command-line tool is present. ElectrumX is not an interactive terminal application; this observation does not establish every possible attack path. |
| [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369), libacl | The package is present. libacl was not observed in the running daemon's mapped libraries during indexing; that snapshot is not a complete reachability audit. |
| util-linux mount/nsenter advisories | Tools are present. The test matched the supplied Compose restrictions: `CapEff=0x2` (only `DAC_OVERRIDE`) and `NoNewPrivs=1`, with no `SYS_ADMIN`. Changing deployment privileges changes this assessment. |

The util-linux entries concern privileged mount or namespace workflows:
[CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642),
[CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408),
[CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409), and
[CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410).
Debian's notes classify several as minor issues without a current stable-security
update; that differs from the scanner's severity labels. Neither label alone proves
network exploitability. No production host or service was changed by this review.

## Dashboard blockers resolved in the optional replacement

The older Debian dashboard did not pass the publication gate. Its three Critical
matches were:

- CVE-2025-7458 — `libsqlite3-0 3.40.1-2+deb12u2`, scanner status `affected`.
- CVE-2026-6653 — `libxml2 2.9.14+dfsg-1.3~deb12u6`, status `fix_deferred`.
- CVE-2023-45853 — `zlib1g 1:1.2.13.dfsg-1`, status `will_not_fix`.

The replacement does not install SQLite and uses newer XML/zlib packages; no
scanner exceptions were added. Debian's tracker documents the older-package
status for [SQLite](https://security-tracker.debian.org/tracker/CVE-2025-7458),
[libxml2](https://security-tracker.debian.org/tracker/CVE-2026-6653) and
[zlib/MiniZip](https://security-tracker.debian.org/tracker/CVE-2023-45853).
In particular, Debian notes that the affected MiniZip code was not built into the
older zlib binary package: the scan match alone did not establish exposure.
The new image passes the same unmodified candidate gate, and has an independent
dashboard-only workflow. Keep the administrative dashboard off the public Internet.
It is optional for ordinary Electrum operation, not a dependency of the daemon.

## Release boundaries

Candidate CI blocks detected secrets, all Critical findings, and fixable High
findings for the daemon. It publishes only explicit `-rc.N` tags and provides an
SBOM and sanitized summaries. Unfixed High findings remain visible. A stable
release needs a fresh scan, review of remaining findings, full-chain/restart
evidence for the chosen digest, and accurate integration limitations.

The third-party Discord bot was not supplied. Standard protocol checks must not
be represented as proof of that bot's end-to-end compatibility.
