# Optional dashboard access boundary

This change is separate from the Brotli/PHP package patch. No public-dashboard
security guarantee is made for the legacy application.

- A missing or shorter-than-20-character runtime password fails closed with HTTP
  503. There is no empty-password authentication bypass and no embedded password.
- The password comes from a Compose secret file, not the image or repository.
- PHP errors are logged rather than exposed in browser responses.
- Session cookies use HttpOnly and SameSite=Strict; strict session-ID handling is
  enabled. Use the private loopback binding through an SSH tunnel, not public HTTP.
- Application source and runtime-data directories deny direct Apache access.
- Access checks do not trust an HTTP Host header as proof of a local client.
  With the default configuration, network restriction is the loopback publish
  and authentication is the runtime password; these are separate controls.

Do not publish port 80/8002 or proxy the dashboard publicly without a separate
review and an additional authenticated boundary. Do not expose admin RPC 8000.
Protect the Docker socket: access to it effectively grants control over containers.

Geolocation is disabled in the baseline configuration so session/client IPs are
not sent to third-party services by default. Persisted dashboard data is private;
exclude it from images, Git, public backups, and support messages.
