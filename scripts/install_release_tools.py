"""Install exact, checksum-verified Linux/amd64 release tools into a local directory."""
import argparse
import hashlib
import io
from pathlib import Path
import platform
import tarfile
import urllib.request

TOOLS = {
    'trivy': ('aquasecurity/trivy', 'v0.76.1', 'trivy_0.76.1_Linux-64bit.tar.gz',
              'c7cbe3137fb8a48a17574bede3dd6beb16742d1e9772929940fc90082c39d9c0'),
    'gitleaks': ('gitleaks/gitleaks', 'v8.30.1', 'gitleaks_8.30.1_linux_x64.tar.gz',
                '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb'),
    'actionlint': ('rhysd/actionlint', 'v1.7.12', 'actionlint_1.7.12_linux_amd64.tar.gz',
                   '8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8'),
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    assert platform.system() == 'Linux' and platform.machine() in ('x86_64', 'AMD64')
    args.directory.mkdir(parents=True, exist_ok=True)
    for name, (repo, version, filename, digest) in TOOLS.items():
        url = f'https://github.com/{repo}/releases/download/{version}/{filename}'
        with urllib.request.urlopen(url, timeout=180) as response:
            archive = response.read()
        assert hashlib.sha256(archive).hexdigest() == digest, f'{name}: checksum mismatch'
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
            member = tar.getmember(name)
            assert member.isfile(), 'Expected one regular executable, not a link'
            payload = tar.extractfile(member).read()
        target = args.directory/name
        target.write_bytes(payload)
        target.chmod(0o755)
        print(f'{name} {version}: checksum verified')

if __name__ == '__main__':
    main()
