import re

def update_0900():
    patch_path = 'xnu/patches/0900-en0-Apple80211-for-wifid-over-the-Topaz.patch'
    with open(patch_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into file diffs
    file_diffs = content.split('diff --git ')
    new_file_diffs = [file_diffs[0]]

    for fd in file_diffs[1:]:
        header_line = fd.split('\n')[0]
        file_name = header_line.split(' ')[0]

        if 'bsd/dev/redwood_apple80211.c' in file_name:
            # 1. Update redwood_apple80211.c get ioctl
            target_apple80211_get = (
                "+\tdefault:\n"
                "+\t\tbreak;\n"
                "+\t}\n"
                "+\n"
                "+\t/* the rest is about the network joined, and there is none unless the station says so */"
            )
            repl_apple80211_get = (
                "+\tcase 29: {                              /* DEAUTH reason/status (16 bytes) */\n"
                "+\t\tuint8_t zero[16] = { 0 };\n"
                "+\t\treturn give(request, zero, sizeof(zero));\n"
                "+\t}\n"
                "+\tcase 51: {                              /* COUNTRY_CODE (3 bytes) */\n"
                "+\t\tconst char cc[4] = \"00\";\n"
                "+\t\treturn give(request, cc, request->req_len < 4 ? request->req_len : 4);\n"
                "+\t}\n"
                "+\tcase 14: {                              /* PHY_MODE (12 bytes) */\n"
                "+\t\tstruct {\n"
                "+\t\t\tuint32_t version;\n"
                "+\t\t\tuint32_t active;\n"
                "+\t\t\tuint32_t supported;\n"
                "+\t\t} answer = { .version = 1, .active = 8 /* 11n */, .supported = 0x3f };\n"
                "+\t\treturn give(request, &answer, sizeof(answer));\n"
                "+\t}\n"
                "+\tcase 17: {                              /* NOISE (same layout as RSSI 16) */\n"
                "+\t\tstruct {\n"
                "+\t\t\tuint32_t version, radios, unit;\n"
                "+\t\t\tint32_t each[4], all, each_ext[4], all_ext;\n"
                "+\t\t} answer = { .version = 1, .radios = 1, .each = { -95 }, .all = -95,\n"
                "+\t\t\t     .each_ext = { -95 }, .all_ext = -95 };\n"
                "+\t\treturn give(request, &answer, sizeof(answer));\n"
                "+\t}\n"
                "+\tdefault:\n"
                "+\t\tbreak;\n"
                "+\t}\n"
                "+\n"
                "+\t/* the rest is about the network joined, and there is none unless the station says so */"
            )
            assert target_apple80211_get in fd, "target_apple80211_get not found"
            fd = fd.replace(target_apple80211_get, repl_apple80211_get, 1)

            # Update set ioctl default
            target_apple80211_set = (
                "+\tcase 10:\n"
                "+\t\treturn set_scan(request, said, said_size);\n"
                "+\tdefault:\n"
                "+\t\treturn EOPNOTSUPP;\n"
                "+\t}"
            )
            repl_apple80211_set = (
                "+\tcase 10:\n"
                "+\t\treturn set_scan(request, said, said_size);\n"
                "+\tdefault:\n"
                "+\t\t/* accept & ignore unknown set requests (e.g. 422, 365, 383, 25, 51) so wifid doesn't abort */\n"
                "+\t\treturn 0;\n"
                "+\t}"
            )
            assert target_apple80211_set in fd, "target_apple80211_set not found"
            fd = fd.replace(target_apple80211_set, repl_apple80211_set, 1)

            # Recalculate line count
            lines = fd.split('\n')
            hunk_idx = [i for i, l in enumerate(lines) if l.startswith('@@ -0,0 +1,')][0]
            added_lines = [l for l in lines[hunk_idx+1:] if l.startswith('+')]
            lines[hunk_idx] = f"@@ -0,0 +1,{len(added_lines)} @@"
            fd = '\n'.join(lines)

        elif 'bsd/dev/redwood_net.c' in file_name:
            # Update net_ioctl
            target_net_ioctl = (
                "+\tcase SIOCSIFADDR:\n"
                "+\t\tifnet_set_flags(ifp, IFF_UP, IFF_UP);\n"
                "+\t\tbreak;\n"
                "+\tcase SIOCSIFFLAGS:\n"
                "+\t\t/* running whenever it is up: the link is there or it is not, nothing is switched on */\n"
                "+\t\tifnet_set_flags(ifp, (ifnet_flags(ifp) & IFF_UP) ? IFF_RUNNING : 0, IFF_RUNNING);\n"
                "+\t\tbreak;"
            )
            repl_net_ioctl = (
                "+\tcase SIOCSIFADDR:\n"
                "+\t\tifnet_set_flags(ifp, IFF_UP | (net_link_up ? IFF_RUNNING : 0), IFF_UP | IFF_RUNNING);\n"
                "+\t\tbreak;\n"
                "+\tcase SIOCSIFFLAGS:\n"
                "+\t\t/* running whenever it is up and the link is active */\n"
                "+\t\tifnet_set_flags(ifp, ((ifnet_flags(ifp) & IFF_UP) && net_link_up) ? IFF_RUNNING : 0, IFF_RUNNING);\n"
                "+\t\tbreak;"
            )
            assert target_net_ioctl in fd, "target_net_ioctl not found"
            fd = fd.replace(target_net_ioctl, repl_net_ioctl, 1)

            # Update redwood_net_link_state
            target_net_link = (
                "+void\n"
                "+redwood_net_link_state(bool up)\n"
                "+{\n"
                "+\tif (net_ifp == NULL || up == net_link_up) {\n"
                "+\t\treturn;\n"
                "+\t}\n"
                "+\tnet_link_up = up;\n"
                "+\tprintf(\"net: the link (%s) is %s\\n\", net_link->name, up ? \"up\" : \"down\");\n"
                "+\tnet_link_event(net_ifp, up ? KEV_DL_LINK_ON : KEV_DL_LINK_OFF);\n"
                "+}"
            )
            repl_net_link = (
                "+void\n"
                "+redwood_net_link_state(bool up)\n"
                "+{\n"
                "+\tif (net_ifp == NULL || up == net_link_up) {\n"
                "+\t\treturn;\n"
                "+\t}\n"
                "+\tnet_link_up = up;\n"
                "+\tprintf(\"net: the link (%s) is %s\\n\", net_link->name, up ? \"up\" : \"down\");\n"
                "+\tif (up) {\n"
                "+\t\tifnet_set_flags(net_ifp, IFF_UP | IFF_RUNNING, IFF_UP | IFF_RUNNING);\n"
                "+\t\tnet_link_event(net_ifp, KEV_DL_LINK_ON);\n"
                "+\t} else {\n"
                "+\t\tifnet_set_flags(net_ifp, 0, IFF_RUNNING);\n"
                "+\t\tnet_link_event(net_ifp, KEV_DL_LINK_OFF);\n"
                "+\t}\n"
                "+}"
            )
            assert target_net_link in fd, "target_net_link not found"
            fd = fd.replace(target_net_link, repl_net_link, 1)

            # Update redwood_net_attach
            target_net_attach = (
                "+\tifnet_set_mtu(ifp, ETHERMTU);\n"
                "+\tifnet_set_flags(ifp, IFF_BROADCAST | IFF_MULTICAST | IFF_SIMPLEX, 0xffff);"
            )
            repl_net_attach = (
                "+\tifnet_set_mtu(ifp, ETHERMTU);\n"
                "+\tifnet_set_flags(ifp, IFF_UP | IFF_BROADCAST | IFF_MULTICAST | IFF_SIMPLEX, 0xffff);"
            )
            assert target_net_attach in fd, "target_net_attach not found"
            fd = fd.replace(target_net_attach, repl_net_attach, 1)

            # Recalculate line count
            lines = fd.split('\n')
            hunk_idx = [i for i, l in enumerate(lines) if l.startswith('@@ -0,0 +1,')][0]
            added_lines = [l for l in lines[hunk_idx+1:] if l.startswith('+')]
            lines[hunk_idx] = f"@@ -0,0 +1,{len(added_lines)} @@"
            fd = '\n'.join(lines)

        elif 'iokit/Kernel/arm/MiniIONetworkStack.cpp' in file_name:
            target_stack = (
                "+\tif (said++ < 4) {\n"
                "+\t\tIOLog(\"MiniIONetworkStack: asked to name an interface: there are none of that kind\\n\");\n"
                "+\t}\n"
                "+\treturn kIOReturnUnsupported;"
            )
            repl_stack = (
                "+\tif (said++ < 4) {\n"
                "+\t\tIOLog(\"MiniIONetworkStack: asked to name an interface\\n\");\n"
                "+\t}\n"
                "+\treturn kIOReturnSuccess;"
            )
            assert target_stack in fd, "target_stack not found"
            fd = fd.replace(target_stack, repl_stack, 1)

            # Recalculate line count
            lines = fd.split('\n')
            hunk_idx = [i for i, l in enumerate(lines) if l.startswith('@@ -0,0 +1,')][0]
            added_lines = [l for l in lines[hunk_idx+1:] if l.startswith('+')]
            lines[hunk_idx] = f"@@ -0,0 +1,{len(added_lines)} @@"
            fd = '\n'.join(lines)

        new_file_diffs.append(fd)

    new_content = 'diff --git '.join(new_file_diffs)
    with open(patch_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Successfully updated patch 0900!")

if __name__ == '__main__':
    update_0900()
