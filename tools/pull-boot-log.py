import subprocess, struct, sys, os

ADB = r"C:\Program Files (x86)\Minimal ADB and Fastboot\adb.exe"

def run_adb(cmd):
    res = subprocess.run([ADB] + cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()

def pull_log(out_txt, out_bin):
    print("Finding userdata partition...", flush=True)
    dev = run_adb(["shell", "for d in /dev/block/by-name/userdata /dev/block/bootdevice/by-name/userdata; do [ -e $d ] && readlink -f $d && break; done"])
    print(f"Userdata dev: {dev}", flush=True)
    if not dev:
        print("Error: userdata not found!", file=sys.stderr)
        return False
    
    bytes_str = run_adb(["shell", "blockdev", "--getsize64", dev])
    total_bytes = int(bytes_str)
    skip = (total_bytes // 4096) - 1025
    print(f"Total bytes: {total_bytes}, skip blocks: {skip}", flush=True)
    
    print(f"Reading 1025 blocks (4MB) to {out_bin}...", flush=True)
    cmd = [ADB, "exec-out", f"dd if={dev} bs=4096 skip={skip} count=1025 2>/dev/null"]
    with open(out_bin, "wb") as f:
        subprocess.run(cmd, stdout=f, check=True)
    
    bin_size = os.path.getsize(out_bin)
    print(f"Downloaded binary log size: {bin_size} bytes", flush=True)
    
    data = open(out_bin, "rb").read()
    magic, version, size, total, seq = struct.unpack_from("<8sIIQQ", data, 0)
    print(f"Header: magic={magic}, version={version}, ring size={size}, total={total}, seq={seq}", flush=True)
    if magic != b"SWEETLOG":
        print("Error: no SWEETLOG header found!", file=sys.stderr)
        return False
    
    ring = data[4096:4096 + size]
    if total <= size:
        text = ring[:total]
    else:
        start = total % size
        text = ring[start:] + ring[:start]
    
    out = text.decode("utf-8", "replace").replace("\r", "")
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Decoded console log written to {out_txt} ({len(out)} chars)", flush=True)
    return True

if __name__ == "__main__":
    out_txt = sys.argv[1] if len(sys.argv) > 1 else "logs/boot-topaz-17.txt"
    out_bin = sys.argv[2] if len(sys.argv) > 2 else "logs/boot-topaz-17.bin"
    os.makedirs(os.path.dirname(out_txt), exist_ok=True)
    pull_log(out_txt, out_bin)
