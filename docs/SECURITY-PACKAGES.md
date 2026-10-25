# PHP and Brotli security update

This change is separate from the source import, database safeguards, and dashboard
authentication hardening. It changes the dashboard's base/runtime packages, not
Electrum RPC or blockchain behavior.

- PHP 8.2.35 is the minimum on the 8.2 branch for CVE-2026-109618 and
  CVE-2026-109619. Review the pin as subsequent security releases arrive.
- Debian bookworm `libbrotli1 1.0.9-2+deb12u1` is the minimum fixed package for
  CVE-2026-111497. PHP/cURL can still report upstream Brotli `1.0.9` because Debian
  backports the fix. Check the complete Debian package version.
- The build fails if the distribution or installed versions do not satisfy those
  checks, including when `PHP_BASE_IMAGE` is overridden.

Reference: <https://security-tracker.debian.org/tracker/CVE-2026-111497>.

```sh
docker compose --profile dashboard build --pull --no-cache dashboard
docker compose exec -T dashboard php -v
docker compose exec -T dashboard dpkg-query -W libbrotli1
```

The `exec` checks apply to a running container; rebuilding alone does not replace
an existing container. After backing up configuration and runtime data, replace
only the dashboard with `docker compose --profile dashboard up -d --no-deps dashboard`.
Verify login, rendering, logs and Electrum health afterward; retain the prior image
and runtime-data backup for rollback. A rollback may reintroduce the vulnerability.

This is not a claim that every dependency is vulnerability-free. Keep scanning
and rebuilding images. A package's presence does not by itself prove an attacker
can reach its decoder in your deployment.
