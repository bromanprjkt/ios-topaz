import struct, re

with open('logs/modem_b.img', 'rb') as f:
    data = f.read()

bytes_per_sector = struct.unpack('<H', data[11:13])[0]
sectors_per_cluster = data[13]
cluster_size = bytes_per_sector * sectors_per_cluster
reserved_sectors = struct.unpack('<H', data[14:16])[0]
fats = data[16]
root_entries = struct.unpack('<H', data[17:19])[0]
sectors_per_fat = struct.unpack('<H', data[22:24])[0]
first_data_sector = reserved_sectors + fats * sectors_per_fat + (root_entries * 32 + bytes_per_sector - 1) // bytes_per_sector

def cluster_to_offset(c):
    return (first_data_sector + (c - 2) * sectors_per_cluster) * bytes_per_sector

fat_offset = reserved_sectors * bytes_per_sector
fat_size = sectors_per_fat * bytes_per_sector
fat_bytes = data[fat_offset:fat_offset+fat_size]
fat = struct.unpack(f'<{len(fat_bytes)//2}H', fat_bytes)

def get_cluster_chain(start_cluster):
    chain = []
    c = start_cluster
    while c >= 2 and c < 0xfff8:
        chain.append(c)
        c = fat[c]
    return chain

def parse_dir(dir_bytes):
    entries = []
    lfn = []
    for i in range(0, len(dir_bytes), 32):
        ent = dir_bytes[i:i+32]
        if ent[0] == 0: break
        if ent[0] == 0xe5: continue
        attr = ent[11]
        if attr == 0x0f:
            name_part = ent[1:11] + ent[14:26] + ent[28:32]
            chars = []
            for j in range(0, len(name_part), 2):
                c = struct.unpack('<H', name_part[j:j+2])[0]
                if c == 0 or c == 0xffff: break
                chars.append(chr(c))
            lfn.append(''.join(chars))
        else:
            if lfn:
                name = ''.join(reversed(lfn))
                lfn = []
            else:
                name = ent[:8].decode('latin1', 'ignore').strip()
                ext = ent[8:11].decode('latin1', 'ignore').strip()
                if ext: name = f'{name}.{ext}'
            cluster = struct.unpack('<H', ent[26:28])[0]
            size = struct.unpack('<I', ent[28:32])[0]
            entries.append((name, attr, cluster, size))
    return entries

device_files_list = []

def walk(dir_cluster, path_prefix):
    chain = get_cluster_chain(dir_cluster)
    dir_bytes = b''.join(data[cluster_to_offset(c):cluster_to_offset(c)+cluster_size] for c in chain)
    entries = parse_dir(dir_bytes)
    for name, attr, cl, sz in entries:
        if name in ('.', '..'): continue
        cur_path = f'{path_prefix}/{name}' if path_prefix else name
        if attr & 0x10:
            walk(cl, cur_path)
        else:
            off = cluster_to_offset(cl) if cl >= 2 else 0
            device_files_list.append((cur_path, sz, off))

walk(2, 'image')

with open('xnu/patches/0121-topaz-modem-host-services.patch', 'r', encoding='utf-8') as f:
    patch_lines = f.readlines()

patch_fw_all = []
for l in patch_lines[778:1436]:
    m = re.search(r'\{\s*"([^"]+)"', l)
    if m:
        patch_fw_all.append(m.group(1))

dev_map = {}
for p, sz, off in device_files_list:
    pl = p.lower()
    if pl not in dev_map:
        dev_map[pl] = []
    dev_map[pl].append((sz, off))

new_fw_ext = []
new_fw_all = []

for idx, p in enumerate(patch_fw_all):
    pl = p.lower()
    if pl not in dev_map or not dev_map[pl]:
        raise ValueError(f'File {p} not found in modem_b')
    sz, off = dev_map[pl].pop(0)
    new_fw_ext.append((off, sz))
    new_fw_all.append((p, sz, idx, 1))

# Generate replacement lines
replacement = []
replacement.append(f'/* generated from device modem_b FAT16: {len(new_fw_all)} files, {len(new_fw_ext)} extents */\n')
replacement.append('static const struct { uint32_t off, len; } fw_ext[] = {\n')
for off, sz in new_fw_ext:
    replacement.append(f'\t{{ 0x{off:x}, 0x{sz:x} }},\n')
replacement.append('};\n')
replacement.append('static const struct { const char *path; uint32_t size; uint16_t ext, next; } fw_all[] = {\n')
for p, sz, idx, n in new_fw_all:
    replacement.append(f'\t{{ "{p}", 0x{sz:x}, {idx}, {n} }},\n')
replacement.append('};\n')

# Prefix with '+' for the patch file format
patch_replacement = ['+' + line for line in replacement]

# Replace lines 118 to 1436 (inclusive)
new_patch_lines = patch_lines[:118] + patch_replacement + patch_lines[1437:]

with open('xnu/patches/0121-topaz-modem-host-services.patch', 'w', encoding='utf-8') as f:
    f.writelines(new_patch_lines)

print('Updated 0121-topaz-modem-host-services.patch successfully!')
