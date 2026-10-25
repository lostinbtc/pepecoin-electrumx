<?php
namespace App;

// Operator-owned runtime secret; never bake a live password into an image.
$passwordFile = getenv('DASHBOARD_PASSWORD_FILE') ?: '/run/secrets/dashboard_password';
$password = is_readable($passwordFile) ? rtrim(file_get_contents($passwordFile), "\r\n") : '';
if (strlen($password) < 20) {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    exit("Dashboard unavailable: configure a strong runtime password file.\n");
}
define('EXD_PASSWORD', $password);
define('EXD_RPC_HOST', getenv('DASHBOARD_RPC_HOST') ?: 'electrumx');
define('EXD_RPC_PORT', (int) (getenv('DASHBOARD_RPC_PORT') ?: '8000'));
unset($password, $passwordFile);

class Config {
    const PASSWORD = EXD_PASSWORD;
    // Compose publishes the dashboard on loopback; authentication is separate.
    const ACCESS_IP = '';
    const RPC_IP = EXD_RPC_HOST;
    const RPC_PORT = EXD_RPC_PORT;
    // Do not send client IPs to third-party geolocation services by default.
    const SESSIONS_GEO = false;
    const PEERS_GEO = false;
    const DISPLAY_BLOCKS = 10;
}
