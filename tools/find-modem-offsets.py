import zlib, subprocess

ADB = r'C:\Program Files (x86)\Minimal ADB and Fastboot\adb.exe'
def sh_bytes(cmd):
    return subprocess.run([ADB, 'exec-out', cmd], capture_output=True).stdout

dump = open('logs/modem_b_device.bin', 'rb').read()

names = [
    'modem.b00', 'modem.b01', 'modem.b02', 'modem.b03', 'modem.b04', 'modem.b05',
    'modem.b06', 'modem.b07', 'modem.b08', 'modem.b09', 'modem.b10', 'modem.b11',
    'modem.b12', 'modem.b14', 'modem.b15', 'modem.b16', 'modem.b17', 'modem.b18',
    'modem.b19', 'modem.b22', 'modem.b23', 'modem.b24', 'modem.b25', 'modem.b26',
    'modem.b27', 'modem.b28', 'modem.b29', 'modem.mdt'
]

print("static const struct { const char *name; uint32_t off, size, crc; } fw_files[] = {")
for name in names:
    content = sh_bytes(f'cat /mnt/modem_b/image/{name}')
    sz = len(content)
    crc = zlib.crc32(content)
    needle = content[:64]
    off = 0
    found_off = None
    while True:
        pos = dump.find(needle, off)
        if pos == -1:
            break
        if pos >= 0x1e00000 and (pos & 0xfff) == 0:
            # Check CRC
            chunk = dump[pos:pos+sz]
            if zlib.crc32(chunk) == crc:
                found_off = pos
                break
        off = pos + 1
    if found_off is not None:
        print(f'\t{{ "{name}", {hex(found_off)}, {hex(sz)}, 0x{crc:08x} }},')
    else:
        # try without 4k alignment requirement
        off = 0
        while True:
            pos = dump.find(needle, off)
            if pos == -1:
                break
            if pos >= 0x1e00000:
                chunk = dump[pos:pos+sz]
                if zlib.crc32(chunk) == crc:
                    found_off = pos
                    break
            off = pos + 1
        if found_off is not None:
            print(f'\t{{ "{name}", {hex(found_off)}, {hex(sz)}, 0x{crc:08x} }},  /* unaligned */')
        else:
            print(f'// NOT FOUND: {name}')
print("};")
