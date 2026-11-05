"""Download and SHA256-verify the portable 3-5 piece Syzygy set."""
import concurrent.futures
import hashlib
import os
from pathlib import Path
import re
import time
import urllib.request

BASE = 'https://tablebase.lichess.ovh/tables/standard/'
DEST = Path(__file__).resolve().parent / 'engines' / 'syzygy' / '3-4-5'

def opener():
    proxy = os.getenv('TABLEBASE_PROXY')
    return urllib.request.build_opener(urllib.request.ProxyHandler({'https': proxy}) if proxy else urllib.request.ProxyHandler())

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def download(item):
    name, expected = item
    path = DEST / name
    if path.exists() and digest(path) == expected:
        return name
    folder = '3-4-5-wdl/' if name.endswith('.rtbw') else '3-4-5-dtz/'
    temporary = path.with_suffix(path.suffix + '.part')
    for attempt in range(3):
        try:
            with opener().open(BASE + folder + name, timeout=90) as response, temporary.open('wb') as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
            if digest(temporary) != expected:
                raise ValueError('SHA256 mismatch: ' + name)
            temporary.replace(path)
            return name
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = opener().open(BASE + 'sha256', timeout=60).read().decode()
    wanted = {}
    for line in manifest.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, name = parts
        if re.fullmatch(r'[KQRBNP]+v[KQRBNP]+\.rtb[wz]', name) and len(name.split('.')[0].replace('v', '')) <= 5:
            wanted[name] = sha
    if len(wanted) != 290:
        raise ValueError(f'Unexpected table count: {len(wanted)}')
    (DEST / 'SHA256SUMS.txt').write_text(''.join(f'{sha}  {name}\n' for name, sha in sorted(wanted.items())))
    print(f'Downloading/verifying {len(wanted)} files to {DEST}', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        tasks = [pool.submit(download, item) for item in wanted.items()]
        for i, task in enumerate(concurrent.futures.as_completed(tasks), 1):
            name = task.result()
            if i % 10 == 0 or i == len(wanted):
                print(f'{i}/{len(wanted)} verified: {name}', flush=True)
    total = sum((DEST / name).stat().st_size for name in wanted)
    print(f'Complete: {len(wanted)} SHA256-verified files, {total} bytes', flush=True)
