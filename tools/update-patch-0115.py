with open('xnu/patches/0115-topaz-modem-fw-from-modem-a.patch', 'r', encoding='utf-8') as f:
    content = f.read()

# Exact table for modem_b:
exact_table = '''static char fw_part[32] = "modem_b";
static const struct { const char *name; uint32_t off, size, crc; } fw_files[] = {
\t{ "modem.b00", 0x1e1d000, 0x414, 0x3bdcec0f },
\t{ "modem.b01", 0x1e21000, 0x1f78, 0x118c5bb8 },
\t{ "modem.b02", 0x1e25000, 0x2930, 0x24a696ac },
\t{ "modem.b03", 0x1e29000, 0x2518, 0x93a2467e },
\t{ "modem.b04", 0x1e2d000, 0x4a3ac, 0x58125a47 },
\t{ "modem.b05", 0x1e79000, 0x119d8, 0x5a8bbe40 },
\t{ "modem.b06", 0x1e8d000, 0x100c, 0x84377dd1 },
\t{ "modem.b07", 0x1e91000, 0x90b4, 0x499e7b81 },
\t{ "modem.b08", 0x1e9d000, 0x4f054, 0x0b14df29 },
\t{ "modem.b09", 0x1eed000, 0x143ee8, 0x1310d97c },
\t{ "modem.b10", 0x2031000, 0x40000, 0x6326f42b },
\t{ "modem.b11", 0x2071000, 0x540, 0xab59447d },
\t{ "modem.b12", 0x2075000, 0xe21f0, 0x3e74d716 },
\t{ "modem.b14", 0x2159000, 0x2d, 0x7a4002c7 },
\t{ "modem.b15", 0x215d000, 0x7c, 0x959b6a58 },
\t{ "modem.b16", 0x215e000, 0x9c1a0, 0xd902be24 },
\t{ "modem.b17", 0x2201000, 0x61110, 0xd2182ca7 },
\t{ "modem.b18", 0x2265000, 0x2d2a09, 0xfa2ef803 },
\t{ "modem.b19", 0x2539000, 0x2d94cc, 0xf841a2c0 },
\t{ "modem.b22", 0x2815000, 0x10ec0, 0xaa322332 },
\t{ "modem.b23", 0x2829000, 0x1722040, 0x4d661cd3 },
\t{ "modem.b24", 0x3f4d000, 0xa07900, 0xf8e11b98 },
\t{ "modem.b25", 0x4955000, 0x7790f, 0x8f676e46 },
\t{ "modem.b26", 0x49cd000, 0x15104, 0x33437cee },
\t{ "modem.b27", 0x49e5000, 0x1378, 0x161303ae },
\t{ "modem.b28", 0x49e9000, 0xb0, 0x1e475201 },
\t{ "modem.b29", 0x49ed000, 0x7d52c, 0x1146af66 },
\t{ "modem.mdt", 0x4a6d000, 0x238c, 0xe6391e32 },
};'''

old_table_start = content.find('+static char fw_part[32] = "modem_b";')
assert old_table_start != -1, "old table start not found"
old_table_end = content.find('+};', old_table_start) + 3

new_table_patch = '\n'.join('+' + l if l else '+' for l in exact_table.split('\n'))
content = content[:old_table_start] + new_table_patch + content[old_table_end:]

# Update check in fw_read:
old_check = '''+\tif (i < 0 || fw_files[i].size > max) {
+\t\tLOG("%s: not in the table or too big (%lld)", name, fw_size(name));
 \t\treturn -1;
 \t}'''

new_check = '''+\tif (i < 0) {
+\t\tLOG("%s: not in the table", name);
+\t\treturn -1;
+\t}
+\tuint64_t to_read = fw_files[i].size;
+\tif (to_read > max) {
+\t\tLOG("%s: size %llu > max %llu: clamping to max", name, to_read, max);
+\t\tto_read = max;
+\t}'''

assert old_check in content, "old_check not found!"
content = content.replace(old_check, new_check)

# Update read call:
old_read_call = '+\terr = sweet_ufs_read_part(fw_part, fw_files[i].off, dst, fw_files[i].size);'
new_read_call = '+\terr = sweet_ufs_read_part(fw_part, fw_files[i].off, dst, to_read);'
assert old_read_call in content, "old_read_call not found!"
content = content.replace(old_read_call, new_read_call)

# Update return value:
old_ret = '+\treturn fw_files[i].size;'
new_ret = '+\treturn (int64_t)to_read;'
assert old_ret in content, "old_ret not found!"
content = content.replace(old_ret, new_ret)

# Update crc check to use to_read instead of fw_files[i].size:
old_crc = '+\tuint32_t crc = crc32(0, dst, fw_files[i].size);'
new_crc = '+\tuint32_t crc = crc32(0, dst, to_read);'
assert old_crc in content, "old_crc not found!"
content = content.replace(old_crc, new_crc)

# Fix hunk counts for patch 0115
import re
lines = content.splitlines(keepends=True)
hunk_regex = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)\n$')

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    m = hunk_regex.match(line)
    if m:
        old_start = int(m.group(1))
        new_start = int(m.group(3))
        trailer = m.group(5)
        
        j = i + 1
        actual_old = 0
        actual_new = 0
        while j < len(lines):
            hl = lines[j]
            if hl.startswith('diff --git') or hunk_regex.match(hl) or hl == '-- \n' or hl.startswith('-- '):
                break
            if hl.startswith('\\ No newline'):
                j += 1
                continue
            if hl.startswith('-'):
                actual_old += 1
            elif hl.startswith('+'):
                actual_new += 1
            elif hl.startswith(' ') or hl == '\n':
                actual_old += 1
                actual_new += 1
            else:
                break
            j += 1
        
        old_part = f"-{old_start},{actual_old}" if actual_old != 1 else f"-{old_start}"
        new_part = f"+{new_start},{actual_new}" if actual_new != 1 else f"+{new_start}"
        new_header = f"@@ {old_part} {new_part} @@{trailer}\n"
        new_lines.append(new_header)
        i += 1
    else:
        new_lines.append(line)
        i += 1

with open('xnu/patches/0115-topaz-modem-fw-from-modem-a.patch', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(new_lines)

print("Patch 0115 successfully updated and validated!")
