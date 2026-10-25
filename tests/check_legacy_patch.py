"""Compare the Brotli-only image with its pinned base without starting either server."""
import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import uuid

BASE = 'emgi2/pepecoin-electrum@sha256:b4325c274ce5aed5ecb42719738a1a5d25a07ef1669ad48551bd85cc6dcb284b'
parser = argparse.ArgumentParser()
parser.add_argument('--image', required=True, help='Locally built Brotli-only image')
args = parser.parse_args()

def docker(*cmd):
    return subprocess.check_output(['docker', *cmd], timeout=60)

def manifest(container, path):
    # Read tar entries in memory, never extract paths from an image onto the host.
    data = docker('cp', container + ':' + path, '-')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive:
            if '__pycache__' in member.name or member.name.endswith('.pyc'):
                continue
            if member.isfile():
                result[member.name] = (member.mode, hashlib.sha256(archive.extractfile(member).read()).hexdigest())
            elif member.issym():
                result[member.name] = ('symlink', member.linkname)
    return result

old = json.loads(docker('image', 'inspect', BASE))[0]
new = json.loads(docker('image', 'inspect', args.image))[0]
for key in ['Entrypoint', 'Cmd', 'Env', 'WorkingDir', 'User', 'ExposedPorts', 'Volumes']:
    assert old['Config'].get(key) == new['Config'].get(key), 'Changed image interface: ' + key
assert old['Architecture'] == new['Architecture'] == 'amd64', 'This check currently covers Linux/amd64 only'
print('Entrypoint, command, environment, workdir, user, declared ports and volumes: unchanged')

created = []
try:
    for image in [BASE, args.image]:
        name = 'pep-legacy-compare-' + uuid.uuid4().hex[:12]
        docker('create', '--name', name, '--network', 'none', '--entrypoint', '/bin/false', image)
        created.append(name)
    for path in ['/entrypoint.sh', '/data/dashboard', '/usr/local/lib/python3.13/site-packages/electrumx']:
        a, b = (manifest(container, path) for container in created)
        assert a == b, 'Changed application files: ' + path
        print(f'{path}: {len(a)} file/symlink entries unchanged')
finally:
    for container in created:
        docker('rm', container)

version = docker('run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
                 '--entrypoint', 'dpkg-query', args.image, '-W', '-f=${Version}', 'libbrotli1').decode().strip()
docker('run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
       '--entrypoint', 'dpkg', args.image, '--compare-versions', version, 'ge', '1.1.0-2+deb13u1')
print('Patched Debian Brotli package:', version)
print('Default server entrypoints were not executed; no database was mounted.')
