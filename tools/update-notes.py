with open('NOTES.md', 'r', encoding='utf-8') as f:
    content = f.read()

new_entry = '''### >>> UPDATE 2026-10-26 16:10 (🎉 CI 40295031323 Succeeded & Booted: IOEthernetInterface & Link State for DHCP / Connection) <<<
- **GitHub Actions Kernel Build 40295031323:**
  - Completed successfully in 5m53s (commit `a983fdf`).
  - Downloaded `xnu-kernel` artifact (`xnu/out/kernel.development.sweet`, 17,994,432 bytes) via chunked streaming downloader `tools/fast-dl.py`.
- **Core Fix Applied (Resolving Wi-Fi Spinning / DHCP Not Connecting):**
  - Subclassed `RedwoodWLAN : public IOEthernetInterface` so Apple's `SystemConfiguration` (`SCNetworkInterfaceCopyAll`) discovers `en0` as a standard Ethernet-type network interface.
  - Published service name as `"en0"`.
  - Attached `IOMACAddress` to both `controller` and `wlan` interfaces.
  - Implemented `RedwoodWLANSetLink(bool up)` to mirror link status to `IOLinkStatus` and `IOInterfaceState` in the IORegistry.
  - Called `RedwoodWLANSetLink(up)` in `bsd/dev/redwood_net.c::redwood_net_link_state`.
  - Implemented `IONetworkStack::setProperties` returning `kIOReturnSuccess`.
- **Boot Image Assembled & Booted to Hardware:**
  - Built `shim/out/payload-wifi.bin` and `shim/out/shim-boot.img` (17,575,936 bytes) with full cmdline:
    `debug=0xc serial=3 cpus=4 keepsyms=1 -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1 sweetfb_noconsole=1 sweetfb_hz=30 sweettouchdelay=2 sweettouchirq=0 modem=1 wifi=1 modem_part=modem_b`
  - Verified device in fastboot (`86104b48 fastboot`) via Minimal Fastboot.
  - Booted device via `& "C:\\Program Files (x86)\\Minimal ADB and Fastboot\\fastboot.exe" boot shim\\out\\shim-boot.img` (0.831s).
- **Next concrete action:** User verifies on device:
  1. Wi-Fi connects to Open Wi-Fi (blue checkmark appears and IP address is acquired via DHCP).
  2. Wi-Fi connects to password-protected network.
  3. Settings > General > About displays storage capacity without crashing.

'''

target = '### >>> UPDATE 2026-10-26 13:05'
idx = content.find(target)
if idx != -1:
    content = content[:idx] + new_entry + content[idx:]
    with open('NOTES.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('NOTES.md successfully updated!')
else:
    print('Target not found!')
