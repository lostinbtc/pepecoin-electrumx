"""Linux Docker integration test: fresh DB, genesis or real chain, verified TLS/WSS.

Full-chain mode requires CHAIN_TEST_DAEMON_URL pointing to an operator-provided
read-only RPC bridge on loopback. It never uses an existing ElectrumX database.
All listening ports are loopback-only; peer discovery/announcement is disabled.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid

from protocol_probe import rpc

def docker(*args, timeout=60):
    return subprocess.check_output(['docker', *args], text=True, stderr=subprocess.STDOUT, timeout=timeout).strip()

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--full-chain', action='store_true')
    parser.add_argument('--timeout-hours', type=float, default=24)
    parser.add_argument('--progress-seconds', type=int, default=120)
    parser.add_argument('--keep-database', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    prefix = 'pep-index-test-' + uuid.uuid4().hex[:10]
    label = 'io.pepecoin.test=' + prefix
    volume = prefix + '-data'
    ports = dict(zip(['tcp', 'tls', 'wss', 'admin'], [free_port() for _ in range(4)]))
    assert len(set(ports.values())) == 4
    fixture = None
    container_created = volume_created = False
    started = time.time()
    tests = Path(__file__).resolve().parent
    image_info = json.loads(docker('image', 'inspect', args.image))[0]
    image_id = image_info['Id']
    info = {'image_id': image_id, 'full_chain': args.full_chain, 'container': prefix,
            'volume': volume, 'ports': ports, 'fresh_database': True, 'passed': False,
            'registry_digests': image_info.get('RepoDigests', []),
            'source_revision': (image_info['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')}

    def save(name, data):
        temp = root / (name + '.tmp')
        temp.write_text(json.dumps(data, indent=2) + '\n')
        temp.replace(root / (name + '.json'))

    def stop(signum, frame):
        raise InterruptedError('Test stopped by operator')

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        if args.full_chain:
            daemon_url = os.environ['CHAIN_TEST_DAEMON_URL']
            url = urllib.parse.urlsplit(daemon_url)
            assert url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost'), 'Use a read-only loopback RPC bridge'
            assert not url.username and not url.password, 'Keep Core credentials in the bridge, not the test'
        else:
            port = free_port()
            daemon_url = f'http://127.0.0.1:{port}'
            fixture = subprocess.Popen([sys.executable, str(tests/'genesis_rpc.py'), '--port', str(port)],
                stdout=(root/'fixture.log').open('w'), stderr=subprocess.STDOUT)

        def core(method, params=None):
            request = urllib.request.Request(daemon_url, data=json.dumps({
                'jsonrpc': '1.0', 'id': 1, 'method': method, 'params': params or []}).encode(),
                headers={'Content-Type': 'application/json'})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request, timeout=90) as response:
                result = json.load(response)
            assert not result.get('error'), result.get('error')
            return result['result']

        for attempt in range(30):
            try:
                chain = core('getblockchaininfo')
                break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError('Read-only Core bridge unavailable')
        assert chain['chain'] == 'main' and not chain['pruned']
        info['initial_core_height'] = chain['blocks']
        save('run', info)
        (root/'certs').mkdir()
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '7',
            '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1',
            '-keyout', str(root/'certs/key.pem'), '-out', str(root/'certs/cert.pem')],
            check=True, capture_output=True)
        docker('volume', 'create', '--label', label, volume)
        volume_created = True
        env = {
            'DB_DIRECTORY': '/data/db', 'COIN': 'Pepecoin',
            'DAEMON_URL': daemon_url.replace('http://', 'http://test:test@', 1),
            'EVENT_LOOP_POLICY': 'uvloop', 'CACHE_MB': '800', 'MAX_SESSIONS': '20',
            'PEER_DISCOVERY': 'off', 'PEER_ANNOUNCE': '',
            'SSL_CERTFILE': '/certs/cert.pem', 'SSL_KEYFILE': '/certs/key.pem',
            'SERVICES': ','.join(f'{protocol}://127.0.0.1:{ports[key]}' for protocol,key in
                [('tcp','tcp'),('ssl','tls'),('wss','wss'),('rpc','admin')]),
        }
        command = ['run', '-d', '--name', prefix, '--label', label, '--network', 'host',
            '--cap-drop', 'ALL', '--cap-add', 'DAC_OVERRIDE',
            '--security-opt', 'no-new-privileges', '--read-only',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m',
            '--cpus', '2', '--memory', '4g', '--memory-swap', '4g', '--pids-limit', '128',
            '--stop-timeout', '300', '--log-opt', 'max-size=30m', '--log-opt', 'max-file=2',
            '-v', volume + ':/data', '-v', str(root/'certs') + ':/certs:ro',
            '-v', str(tests/'protocol_probe.py') + ':/protocol_probe.py:ro']
        for key, value in env.items():
            command += ['-e', key + '=' + value]
        docker(*command, image_id)
        container_created = True
        last_print = 0
        deadline = time.monotonic() + args.timeout_hours * 3600
        while time.monotonic() < deadline:
            assert docker('inspect', '--format', '{{.State.Running}}', prefix) == 'true', 'ElectrumX exited'
            if args.full_chain and shutil.disk_usage(root).free < 50 * 1024**3:
                raise RuntimeError('Local disk safety threshold reached')
            try:
                admin = rpc(ports['admin'], 'getinfo')
            except OSError:
                time.sleep(1)
                continue
            tip = core('getblockcount')
            logs = docker('logs', '--tail', '200', prefix)
            heights = re.findall(r'our height: ([\d,]+)', logs)
            processed = max(admin['db height'], int(heights[-1].replace(',', '')) if heights else -1)
            status = {'phase': 'indexing', 'core_height': tip, 'processed_height': processed,
                      'persisted_height': admin['db height'], 'elapsed_seconds': int(time.time()-started)}
            save('status', status)
            if time.monotonic() - last_print >= args.progress_seconds:
                print(json.dumps(status), flush=True)
                last_print = time.monotonic()
            if admin['db height'] == tip:
                try:
                    rpc(ports['tcp'], 'server.version', ['release-test', '1.4'])
                    break
                except OSError:
                    pass
            time.sleep(15 if args.full_chain else 1)
        else:
            raise TimeoutError('Index did not reach Core tip before test deadline')

        def check():
            height = min(core('getblockcount'), rpc(ports['admin'], 'getinfo')['db height'])
            block_hash = core('getblockhash', [height])
            command = ['exec', prefix, 'python', '/protocol_probe.py', '--height', str(height),
                       '--block-hash', block_hash]
            for key in ['tcp','tls','wss']:
                command += ['--' + key, str(ports[key])]
            if height > 0:
                block = core('getblock', [block_hash, True])
                command += ['--txid', block['tx'][0]]
            return {'height': height, 'block_hash': block_hash,
                    'protocols': json.loads(docker(*command, timeout=180))}

        info['before_restart'] = check()
        docker('restart', '--timeout', '300', prefix, timeout=330)
        for attempt in range(150):
            try:
                height = rpc(ports['tcp'], 'blockchain.headers.subscribe')['height']
                if height >= info['before_restart']['height']:
                    break
            except OSError:
                pass
            time.sleep(2)
        else:
            raise TimeoutError('Persisted database did not recover after restart')
        info['after_restart'] = check()
        assert docker('inspect', '--format', '{{.RestartCount}}', prefix) == '0'
        logs = docker('logs', prefix)
        assert not re.search(r'(?:ERROR:|CRITICAL:|Traceback \(most recent call)', logs), 'Review ElectrumX error log'
        info['passed'] = True
        info['elapsed_seconds'] = int(time.time()-started)
        save('result', info)
        save('status', {'phase':'passed', 'height':info['after_restart']['height'], 'image_id':image_id})
        print(json.dumps(info), flush=True)
    except BaseException as exc:
        # Never include configuration or credential-bearing URLs in reports.
        save('status', {'phase':'stopped' if isinstance(exc, InterruptedError) else 'failed',
                        'error_type':type(exc).__name__})
        if isinstance(exc, InterruptedError):
            print('Operator requested stop; flushing and cleaning up the test service.', flush=True)
            raise SystemExit(130)
        raise
    finally:
        if container_created:
            docker('stop', '--timeout', '300', prefix, timeout=330)
            (root/'electrumx.log').write_text(docker('logs', prefix))
            docker('rm', prefix)
        if volume_created and not args.keep_database:
            docker('volume', 'rm', volume)
        if fixture:
            fixture.terminate()
            fixture.wait(timeout=15)

if __name__ == '__main__':
    main()
