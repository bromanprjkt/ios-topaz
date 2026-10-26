with open('NOTES.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = '''### >>> UPDATE 2026-10-26 13:05 (🎉 CI 40276947589 Succeeded & Booted: HFS vfsops Static Region Panic Fixed) <<<
- **GitHub Actions Kernel Build 40276947589:**
  - Completed successfully in 5m12s (commit `cecd080`).
  - Downloaded `xnu-kernel` artifact (`xnu/out/kernel.development.sweet`, 18,035,800 bytes).
- **Core Fix Verified in Kernel Mach-O Symbols:**
  - `_sweet_vfsops` mapped to `0xfffffe0008117d00` in `__DATA` (writable BSS), completely outside the read-only `__DATA_CONST` static region (`0xfffffe0007180000 - 0xfffffe0007308000`).
  - Completely resolves `panic(cpu 0 caller 0xfffffe0007b8b0dc): Unexpected fault in kernel static region at pc sweet_hfs_register far _hfs_vfsops+0x28`.
- **Boot Image Assembled & Booted to Hardware:**
  - Built `shim/out/payload-wifi.bin` and `shim/out/shim-boot.img` (17,633,280 bytes) with full cmdline:
    `debug=0xc serial=3 cpus=4 keepsyms=1 -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1 sweetfb_noconsole=1 sweetfb_hz=30 sweettouchdelay=2 sweettouchirq=0 modem=1 wifi=1 modem_part=modem_b`
  - Rebooted device from OrangeFox recovery to fastboot via `Minimal ADB and Fastboot`.
  - Booted device via `& "C:\\Program Files (x86)\\Minimal ADB and Fastboot\\fastboot.exe" boot shim\\out\\shim-boot.img` (0.820s).
- **Next concrete action:** User tests:
  1. Open Wi-Fi connection (verify DHCP acquisition and checkmark).
  2. Password-protected Wi-Fi connection (verify WPA2 association and join).
  3. Settings > General > About (verify page opens smoothly and displays partition storage capacity).

'''

target = '### >>> UPDATE 2026-10-26 12:40'
idx = content.find(target)
if idx != -1:
    content = content[:idx] + new_entry + content[idx:]
    with open('NOTES.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("NOTES.md successfully updated!")
else:
    print("Target not found!")
