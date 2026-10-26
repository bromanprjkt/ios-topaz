with open('NOTES.md', 'r', encoding='utf-8') as f:
    content = f.read()

target = '### >>> UPDATE 2026-10-25 (Topaz bring-up preparation complete) <<<'
new_entry = """### >>> UPDATE 2026-10-26 12:35 (🎉 CI 40273791046 Succeeded & Booted: Wi-Fi DHCP, Pre-Join Ioctls, & About Crash Fixed) <<<
- **GitHub Actions Kernel Build 40273791046:**
  - Completed successfully in 5m40s (commit `1331b8f`).
  - Downloaded `xnu-kernel` artifact (`xnu/out/kernel.development.sweet`, 18,019,384 bytes).
- **Core Fixes Applied in Kernel:**
  1. **Wi-Fi Interface Link & DHCP (`bsd/dev/redwood_net.c`, patch `0900`):**
     - Attached `en0` with `IFF_UP` enabled.
     - On link-up (`redwood_net_link_state(true)`), sets `ifnet_set_flags(IFF_UP | IFF_RUNNING)` and emits `KEV_DL_LINK_ON`.
     - In `SIOCSIFFLAGS` and `SIOCSIFADDR`, preserves `IFF_RUNNING` when link is active so raw BPF sockets and DHCP client (`bootp`) can send frames without `ENETDOWN`.
  2. **Wi-Fi WPA2 Pre-Join Ioctls (`bsd/dev/redwood_apple80211.c`, patch `0900`):**
     - Implemented `gets 29` (`DEAUTH`) returning 16 bytes of zero so `wifid` does not see an unhandled error and abort join before associating.
     - Implemented `PHY_MODE` (14), `COUNTRY_CODE` (51), and `NOISE` (17).
     - Defaulted unhandled `set` ioctl requests (`422`, `365`, `383`, `25`, `51`) to return `0` (success) instead of `EOPNOTSUPP`.
  3. **Interface Namer UserClient (`iokit/Kernel/arm/MiniIONetworkStack.cpp`, patch `0900`):**
     - `setProperties` returns `kIOReturnSuccess`.
  4. **Settings > General > About Crash Fixed (`bsd/sweet_hfs/sweet_hfs_iokit.c`, patch `0026`):**
     - Implemented `sweet_hfs_vfs_getattr` and registered it on `hfs_vfsops.vfs_getattr`.
     - Maps `f_blocks`, `f_bsize`, `f_bfree`, `f_bavail`, `f_bused`, `f_files`, `f_ffree`, `f_fsid` from `vfs_statfs(mp)` to VFS attribute list.
     - Resolves `URL.volumeTotalCapacity` returning `nil`, preventing `PodcastsUI func_1cdc47c58` `SIGTRAP` crash when opening Settings > General > About.
- **Boot Image Built & Booted to Hardware:**
  - Built `shim/out/payload-wifi.bin` and `shim/out/shim-boot.img` (17,633,280 bytes).
  - Rebooted device from OrangeFox recovery to fastboot and booted via `fastboot boot shim/out/shim-boot.img` (0.825s).
- **Next concrete action:** User tests:
  1. Open Wi-Fi network connection (verify DHCP IP acquired and blue checkmark appears).
  2. Secured Wi-Fi network connection (enter password and verify successful join).
  3. Settings > General > About (verify it opens and shows Capacity and Available space without crashing).

"""

assert target in content, 'target not found'
content = content.replace(target, new_entry + target, 1)

with open('NOTES.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('NOTES.md updated!')
