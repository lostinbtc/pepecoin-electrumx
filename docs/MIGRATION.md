# Migrating from the legacy combined image

Do not replace the image name blindly. The old image starts Apache and ElectrumX
in one container; this project uses two services, with the dashboard optional.

## Before changing anything

- Record the old image digest, container name, environment and mount destinations
  privately. Do not paste credentials into issues or support channels.
- Preserve the old image, certificates, configuration, and a consistent database
  backup. Stop the old ElectrumX cleanly before snapshotting its database.
- Determine whether your bot uses public Electrum methods, admin RPC, dashboard
  HTTP, Docker names, or restart/reindex commands. Test each actual dependency.

## Storage and configuration

The old image's documented example mounted its database at `/data/db`. Our named
volume is mounted at `/data`, with `DB_DIRECTORY=/data/db`. An old volume whose
root contains the database therefore cannot simply be mounted at our `/data`.
Check the actual layout; stage a copy with the correct `db/` nesting, or use a
fresh index. Never point two running ElectrumX processes at the same database.

Our dashboard lives at `/var/www/html` in its own container, not `/data/dashboard`
in the daemon. It is bound to host loopback 8002, protected with an operator-created
secret file, and stores runtime data in its own named volume. Do not import old
passwords, geolocation caches, or session records into an image.

Use your own Core RPC endpoint, credentials, certificates, and public hostname.
Compose service names are `electrumx` and `dashboard`; generated container names
depend on the project name. Bot commands using a hard-coded old container name
need adjustment. Admin RPC port 8000 stays unpublished.

## Staging and cutover

Build first. Test with a separate project, isolated database copy, and alternate
host ports so the live instance is unaffected. Stage read-only bot operations;
disable its restart/reindex and Discord-writing actions until validated.

Require successful protocol negotiation and header-height checks on TCP, verified
TLS, and WSS; a matching chain/genesis; database height caught up with Core;
working administrative `getinfo` for an authorized local monitor; and dashboard
login if your bot depends on HTTP. Source similarity is not end-to-end bot testing.

At cutover, stop the old service cleanly, take a final backup, and start the new
service with the chosen data copy. Keep the untouched old image and backup for
rollback. Do not assume a database modified by any future release is backwards
compatible. Review startup compaction behavior before the first start.
