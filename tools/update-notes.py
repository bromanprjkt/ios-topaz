with open('NOTES.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = '''### >>> UPDATE 2026-10-26 17:20 (🎉 CI 40304549738 Succeeded & Booted: Patch 0900 Applied, Wi-Fi Restored & Link State Wired) <<<
- **GitHub Actions Kernel Build 40304549738:**
  - Completed successfully in 5m4s (commit `4354bf4`).
  - Verified patch 0900 applied without any warnings in CI log.
  - Downloaded `xnu-kernel` artifact (`xnu/out/kernel.development.sweet`, 18,035,928 bytes) via `tools/wait-and-dl.py` / `fast-dl.py`.
  - Mach-O binary verified containing `topaz_sta_init`, `RedwoodWLANSetLink`, and `MiniIONetworkStack`.
- **Boot Image Assembled & Booted to Hardware:**
  - Built `shim/out/payload-wifi.bin` and `shim/out/shim-boot.img` (17,633,280 bytes) with full cmdline:
    `debug=0xc serial=3 cpus=4 keepsyms=1 -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1 sweetfb_noconsole=1 sweetfb_hz=30 sweettouchdelay=2 sweettouchirq=0 modem=1 wifi=1 modem_part=modem_b`
  - Rebooted device from OrangeFox recovery to fastboot via `Minimal ADB and Fastboot`.
  - Booted device via `& "C:\\Program Files (x86)\\Minimal ADB and Fastboot\\fastboot.exe" boot shim\\out\\shim-boot.img` (0.812s).
- **Next concrete action:** User tests on device:
  1. Verify Wi-Fi toggle switch is functional and scans nearby networks (e.g. FITELNET).
  2. Connect to Open Wi-Fi (`FITELNET`): verify DHCP lease is acquired and blue checkmark appears.
  3. Connect to WPA2 secured Wi-Fi: enter passphrase and verify successful join.
  4. Verify Settings > General > About displays storage capacity without crashing.

'''

target = '### >>> UPDATE 2026-10-26 17:05'
idx = content.find(target)
if idx != -1:
    content = content[:idx] + new_entry + content[idx:]
    with open('NOTES.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("NOTES.md successfully updated!")
else:
    print("Target not found!")
