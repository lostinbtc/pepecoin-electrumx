"""Docker integration check using isolated synthetic RPC; never touches live data."""
import argparse
import http.cookiejar
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

parser = argparse.ArgumentParser()
parser.add_argument('--dashboard-image', required=True)
parser.add_argument('--python-image', required=True)
parser.add_argument('--populated', action='store_true', help='Test synthetic sessions and peers as well')
args = parser.parse_args()
root = Path(__file__).resolve().parent
prefix = 'pep-release-check-' + uuid.uuid4().hex[:10]
network = prefix + '-net'
created = []
data_volume = prefix + '-data'

def docker(*cmd):
    return subprocess.check_output(['docker', *cmd], text=True, stderr=subprocess.STDOUT, timeout=45).strip()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def client():
    return urllib.request.build_opener(NoRedirect(), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

def fetch(opener, url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        response = opener.open(req, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, response.headers, response.read().decode()

def start(name, *params):
    docker('run', '-d', '--name', name, '--network', network, *params)
    created.append(name)

def url(name):
    mapping = json.loads(docker('inspect', '--format', '{{json .NetworkSettings.Ports}}', name))
    return 'http://127.0.0.1:' + mapping['80/tcp'][0]['HostPort'] + '/'

# Dedicated test bridge; only the dashboard is published, on host loopback.
# Some Docker versions suppress published ports on an internal-only network.
docker('network', 'create', network)
docker('volume', 'create', '--label', 'io.pepecoin.test=' + prefix, data_volume)
try:
    start(prefix + '-rpc', '--network-alias', 'fixture-rpc', '--entrypoint', 'python',
          '-v', str(root / 'mock_rpc.py') + ':/mock_rpc.py:ro', args.python_image, '/mock_rpc.py',
          *(['--populated'] if args.populated else []))
    for authenticated in [False, True]:
        name = prefix + ('-configured' if authenticated else '-unconfigured')
        params = ['-p', '127.0.0.1::80', '-e', 'DASHBOARD_RPC_HOST=fixture-rpc',
                  '--read-only', '--security-opt', 'no-new-privileges',
                  '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m',
                  '--tmpfs', '/run/apache2:rw,noexec,nosuid,size=8m',
                  '-v', data_volume + ':/var/www/html/data']
        if authenticated:
            params += ['-v', str(root / 'fixtures/dashboard_password') + ':/run/secrets/dashboard_password:ro']
        start(name, *params, args.dashboard_image)
        base, opener = url(name), client()
        for attempt in range(20):
            try:
                status, headers, body = fetch(opener, base)
                break
            except (OSError, urllib.error.URLError):
                time.sleep(0.25)
        else:
            raise AssertionError('Dashboard failed to listen')
        if not authenticated:
            assert status == 503, status
            assert fetch(opener, base, headers={'Host': 'localhost'})[0] == 503
            print('Missing password and spoofed localhost Host: fail closed PASS')
            continue
        assert status == 302 and 'login.html' in headers.get('Location', '')
        assert fetch(opener, base, data=b'password=wrong')[0] == 302
        password = (root / 'fixtures/dashboard_password').read_text().strip()
        status, headers, body = fetch(opener, base, data=urllib.parse.urlencode({'password': password}).encode())
        assert status == 200 and 'Block Height' in body and re.search(r'>\s*synced\s*<', body)
        assert 'Server offline or incorrect RPC data' not in body
        assert 'https://github.com/lostinbtc/pepecoin-electrumx' in body
        assert 'Dashboard by Mr Bachelor' not in body
        for path in ['', '?p=sessions', '?p=peers', '?p=about']:
            code, _, page = fetch(opener, base + path)
            assert code == 200, (path, code)
            assert 'Server offline or incorrect RPC data' not in page
            if args.populated and path == '?p=sessions':
                assert 'fixture-client' in page
            if args.populated and path == '?p=peers':
                assert 'peer.example.invalid' in page
        for path in ['data/hoster.json', 'src/Config.php', 'views/main.php', '.htaccess']:
            assert fetch(opener, base + path)[0] == 403, path
        assert fetch(client(), base + '?p=sessions')[0] == 302
        docker('exec', '--user', '33:33', name, 'php84', '-r',
               'if (file_put_contents("data/release-test.txt", "retained") === false) exit(1);')
        docker('restart', '--timeout', '30', name)
        # Docker may assign a different ephemeral published port after restart.
        base = url(name)
        for attempt in range(30):
            try:
                if fetch(client(), base)[0] == 302:
                    break
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(0.25)
        else:
            raise AssertionError('Dashboard did not recover after restart:\n' + docker('logs', name)[-4000:])
        status, _, body = fetch(client(), base, data=urllib.parse.urlencode({'password': password}).encode())
        assert status == 200 and 'Block Height' in body
        assert docker('exec', '--user', '33:33', name, 'php84', '-r',
                      'echo file_get_contents("data/release-test.txt");') == 'retained'
        logs = docker('logs', name)
        errors = [line for line in logs.splitlines()
                  if re.search(r'PHP (?:Fatal error|Warning|Parse error|Deprecated)', line)]
        assert not errors, 'Synthetic fixture PHP errors:\n' + '\n'.join(errors)
        print('Login, pages, protected paths, UID-33 data writes, clean restart/persistence: PASS',
              '(populated)' if args.populated else '(empty)')
finally:
    # Exact, randomly named resources created by this check only.
    for name in reversed(created):
        docker('rm', '-f', name)
    docker('volume', 'rm', data_volume)
    docker('network', 'rm', network)
