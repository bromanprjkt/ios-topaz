with open('NOTES.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = '''### >>> UPDATE 2026-10-26 17:05 (Boot 17 Diagnostics Pulled: Root Cause Found in Patch 0900 Skip) <<<
- **Hardware Boot 17 Diagnostics Pulled (`logs/boot-topaz-17.txt`, 650 KB):**
  - Pulled persistent SWEET console log via ADB from OrangeFox recovery.
  - Confirmed modem firmware started and scanned (`TopazModem: t=4057 ms: wlan: radio ready for the rest of the kernel`, found `FITELNET` and `WIFI BUMDES`), but `topaz_sta_init()`, `en0`, and `RedwoodWLAN` never executed.
  - Root Cause Diagnosed from CI Build 40295031323 logs:
    `[warning] Skipping patch .../0900-en0-Apple80211-for-wifid-over-the-Topaz.patch: error: corrupt patch at line 1211`
    Because patch 0900 had a line-count mismatch in hunk headers, GitHub Actions skipped the patch entirely, producing a kernel without any Wi-Fi driver code.
- **Fix Applied in `xnu/patches/0900-en0-Apple80211-for-wifid-over-the-Topaz.patch`:**
  - Recalculated and corrected all hunk line counts.
  - Verified `git apply --check` passes cleanly across all files in patch 0900.
  - Preserved the working `RedwoodWLAN` service name and `IONetworkInterface` class.
  - Implemented `RedwoodWLANSetLink(bool up)` setting `IOLinkStatus = 3` (active) and `IOInterfaceState = 3` (running) to trigger `configd` DHCP discovery, plus `IOMACAddress` on `wlan`.
- **Next concrete action:** Push commit to trigger GitHub Actions build, download kernel, rebuild shim-boot.img, and boot to device.

'''

target = '### >>> UPDATE 2026-10-26 16:10'
idx = content.find(target)
if idx != -1:
    content = content[:idx] + new_entry + content[idx:]
    with open('NOTES.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("NOTES.md successfully updated!")
else:
    print("Target not found!")
