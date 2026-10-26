import urllib.request, json, os, zipfile, io, sys, subprocess, time

def get_token():
    if 'GH_TOKEN' in os.environ:
        return os.environ['GH_TOKEN']
    try:
        res = subprocess.run([sys.executable, 'tools/gh-helper.py', 'auth', 'token'], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        pass
    try:
        res = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        print('Error getting token:', e, file=sys.stderr)
        sys.exit(1)

def download_run_artifact(run_id, artifact_name='xnu-kernel', out_dir='xnu/out'):
    token = get_token()
    url = f'https://api.github.com/repos/bromanprjkt/ios-topaz/actions/runs/{run_id}/artifacts'
    req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'User-Agent': 'Python'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    print('Artifacts found:', len(data.get('artifacts', [])))

    class NoAuthRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
            if new_req and 'Authorization' in new_req.headers:
                del new_req.headers['Authorization']
            return new_req

    opener = urllib.request.build_opener(NoAuthRedirectHandler)

    for a in data.get('artifacts', []):
        print(f"  {a['name']}: id={a['id']}, size={a['size_in_bytes']}")
        if a['name'] == artifact_name:
            dl_url = a['archive_download_url']
            print('  Downloading from', dl_url, flush=True)
            dl_req = urllib.request.Request(dl_url, headers={'Authorization': f'token {token}', 'User-Agent': 'Python'})
            t0 = time.time()
            with opener.open(dl_req, timeout=60) as dl_resp:
                chunks = []
                total = 0
                expected = a['size_in_bytes']
                while True:
                    chunk = dl_resp.read(512 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    speed = total / (time.time() - t0 + 0.001) / (1024 * 1024)
                    print(f"\r  Downloaded {total / 1024 / 1024:.1f} / {expected / 1024 / 1024:.1f} MB ({speed:.2f} MB/s)", end="", flush=True)
                print()
                zip_bytes = b"".join(chunks)
            print('  Downloaded bytes:', len(zip_bytes))
            os.makedirs(out_dir, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                z.extractall(out_dir)
            print(f'  Extracted {artifact_name} into {out_dir}/')
            return True
    return False

if __name__ == '__main__':
    run_id = sys.argv[1] if len(sys.argv) > 1 else '40295031323'
    out = sys.argv[2] if len(sys.argv) > 2 else 'xnu/out'
    success = download_run_artifact(run_id, out_dir=out)
    if not success:
        sys.exit(1)
