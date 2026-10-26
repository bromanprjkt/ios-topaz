import os

new_entry = '''### >>> UPDATE 2026-10-26 12:40 (Fixed Payload Cmdline Truncation & Booted via Minimal Fastboot) <<<
- **Issue Diagnosed (Stuck Progress Bar & Missing Log Console):**
  - In the previous payload generation step, `tools/mkpayload.py` `--cmdline` was called with only `sweetfb_hz=30 sweettouchdelay=2 sweettouchirq=0 modem=1 wifi=1 modem_part=modem_b`.
  - Because `mkpayload.py` replaces the full 608-byte boot-args buffer instead of appending, critical baseline parameters were stripped:
    1. `-noprogress`: When absent, iOS launchd triggers `ProgressUI` to draw an on-screen Apple loading bar.
    2. `ufsrw=1 rootrw=1`: Mounts UFS and root filesystem read-write. Without this, rootfs was mounted read-only, preventing system daemons from initializing.
    3. `cpus=4`: Multi-core boot. Defaulted to single CPU core (extreme boot delay).
    4. `wdt=-1` & `wdt_test=no_user_checkin`: Disables iOS watchdog timeouts.
    5. `debug=0xc serial=3 keepsyms=1`: Kernel debug and serial console output.
  - Additionally, previous turn used `miflash_unlock` fastboot due to PATH resolution. Going forward, the exact path `C:\\Program Files (x86)\\Minimal ADB and Fastboot\\fastboot.exe` is strictly used.
- **Fix Applied & Boot Executed:**
  - Rebuilt `shim/out/payload-wifi.bin` and `shim/out/shim-boot.img` with the complete, unabridged cmdline:
    `debug=0xc serial=3 cpus=4 keepsyms=1 -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1 sweetfb_noconsole=1 sweetfb_hz=30 sweettouchdelay=2 sweettouchirq=0 modem=1 wifi=1 modem_part=modem_b`
  - Rebooted device from recovery to fastboot via `C:\\Program Files (x86)\\Minimal ADB and Fastboot\\adb.exe`.
  - Booted device via `& "C:\\Program Files (x86)\\Minimal ADB and Fastboot\\fastboot.exe" boot shim\\out\\shim-boot.img` (0.809s).
- **Next concrete action:** User observes display booting cleanly without the stuck loading bar into SpringBoard home screen, and verifies Wi-Fi join & Settings > General > About.

'''

with open('NOTES.md', 'r', encoding='utf-8') as f:
    content = f.read()

target = '### >>> UPDATE 2026-10-26 12:35'
idx = content.find(target)
if idx != -1:
    content = content[:idx] + new_entry + content[idx:]
    with open('NOTES.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("NOTES.md successfully updated!")
else:
    print("Target not found!")
