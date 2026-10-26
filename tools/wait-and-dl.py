import time, sys, os, subprocess, json, urllib.request

run_id = sys.argv[1] if len(sys.argv) > 1 else '40304549738'

sys.path.insert(0, 'tools')
fast_dl = __import__('fast-dl')

token = fast_dl.get_token()

print(f"Monitoring GitHub Actions Run {run_id}...", flush=True)
url = f"https://api.github.com/repos/bromanprjkt/ios-topaz/actions/runs/{run_id}"

while True:
    try:
        req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'User-Agent': 'Python'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        status = data.get('status')
        conclusion = data.get('conclusion')
        print(f"[{time.strftime('%H:%M:%S')}] Status: {status}, conclusion: {conclusion}", flush=True)
        if status == 'completed':
            if conclusion == 'success':
                print("Run succeeded! Downloading artifact...", flush=True)
                ok = fast_dl.download_run_artifact(run_id, out_dir='xnu/out')
                if ok:
                    print("Artifact successfully downloaded and extracted!", flush=True)
                    sys.exit(0)
                else:
                    print("Failed to find artifact!", flush=True)
                    sys.exit(1)
            else:
                print(f"Run finished with conclusion: {conclusion}", flush=True)
                sys.exit(1)
    except Exception as e:
        print("Error checking status:", e, flush=True)
    time.sleep(25)
