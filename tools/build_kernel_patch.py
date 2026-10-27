import struct

with open('xnu/out/kernel.development.sweet.orig', 'rb') as f:
    data = bytearray(f.read())

# 1. IOEthernetInterface string and en0 string
str_bytes = b'IOEthernetInterface\x00en0\x00\x00'
data[0x156e5b : 0x156e5b + len(str_bytes)] = str_bytes

# 2. RedwoodWLAN publish("en0") at 0xb02b38
# add x1, x1, #0xe6f ("en0")
struct.pack_into('<I', data, 0xb02b38, 0x9139bc21)

def encode_bl(pc, target):
    delta = (target - pc) // 4
    return 0x94000000 | (delta & 0x3ffffff)

def encode_b(pc, target):
    delta = (target - pc) // 4
    return 0x14000000 | (delta & 0x3ffffff)

def encode_adr(pc, target, rd):
    delta = target - pc
    immlo = delta & 3
    immhi = (delta >> 2) & 0x7ffff
    return 0x10000000 | (immlo << 29) | (immhi << 5) | rd

def encode_adrp(pc, page, rd):
    delta = ((page >> 12) - (pc >> 12)) & 0x1fffff
    immlo = delta & 3
    immhi = (delta >> 2) & 0x7ffff
    return 0x90000000 | (immlo << 29) | (immhi << 5) | rd

def encode_cbz(pc, target, rt):
    delta = (target - pc) // 4
    return 0x34000000 | ((delta & 0x7ffff) << 5) | rt

# 3. topaz_sta_init at 0x52e030:
topaz_sta_init = {}
topaz_sta_init[0x52e030] = 0xa9bf7bfd # stp x29, x30, [sp, #-16]!
topaz_sta_init[0x52e034] = 0x910003fd # mov x29, sp
topaz_sta_init[0x52e038] = encode_bl(0x52e038, 0x52e0bc) # bl early_attach_and_start
topaz_sta_init[0x52e03c] = encode_adrp(0x52e03c, 0xcdc000, 8) # adrp x8, 0xcdc000
topaz_sta_init[0x52e040] = encode_adr(0x52e040, 0x52e060, 9) # adr x9, sta_ready
topaz_sta_init[0x52e044] = 0xd503201f # nop
topaz_sta_init[0x52e048] = 0xd503201f # nop
topaz_sta_init[0x52e04c] = 0xf9079109 # str x9, [x8, #3872] (topaz_wlan_ready_hook = sta_ready)
topaz_sta_init[0x52e050] = 0xa8c17bfd # ldp x29, x30, [sp], #16
topaz_sta_init[0x52e054] = 0xd65f03c0 # ret
topaz_sta_init[0x52e058] = 0xd503201f # nop
topaz_sta_init[0x52e05c] = 0xd503201f # nop

for addr, insn in topaz_sta_init.items():
    struct.pack_into('<I', data, addr, insn)

# 4. sta_bring_up at 0x52e0a0:
sta_bring_up = {}
sta_bring_up[0x52e0a0] = encode_adrp(0x52e0a0, 0xcdc000, 8) # adrp x8, 0xcdc000
sta_bring_up[0x52e0a4] = encode_adr(0x52e0a4, 0x52e130, 9)   # adr x9, sta_rx
sta_bring_up[0x52e0a8] = 0xf9079509                          # str x9, [x8, #3880] (topaz_wlan_rx_hook)
sta_bring_up[0x52e0ac] = encode_adr(0x52e0ac, 0x52e140, 9)   # adr x9, sta_link_changed
sta_bring_up[0x52e0b0] = 0xf9079909                          # str x9, [x8, #3888] (topaz_wlan_link_hook)
sta_bring_up[0x52e0b4] = encode_bl(0x52e0b4, 0x4ca7c0)      # bl current_thread
sta_bring_up[0x52e0b8] = encode_b(0x52e0b8, 0x3a6390)       # b thread_terminate

for addr, insn in sta_bring_up.items():
    struct.pack_into('<I', data, addr, insn)

# 5. early_attach_and_start at 0x52e0bc:
early_attach = {}
early_attach[0x52e0bc] = 0xa9be4ff4 # stp x20, x19, [sp, #-32]!
early_attach[0x52e0c0] = 0xa9017bfd # stp x29, x30, [sp, #16]
early_attach[0x52e0c4] = 0x910043fd # add x29, sp, #0x10
early_attach[0x52e0c8] = encode_adrp(0x52e0c8, 0xc21000, 19) # adrp x19, 0xc21000
early_attach[0x52e0cc] = 0x911ac273                          # add x19, x19, #0x6b0 (&sta_link)
early_attach[0x52e0d0] = 0x91002260                          # add x0, x19, #8 (sta_link.address)
early_attach[0x52e0d4] = encode_bl(0x52e0d4, 0xae84e0)      # bl topaz_wlan_address
early_attach[0x52e0d8] = 0xb9400a68                          # ldr w8, [x19, #8]
early_attach[0x52e0dc] = encode_adrp(0x52e0dc, 0xc21000, 10) # adrp x10, 0xc21000
early_attach[0x52e0e0] = 0x911c214a                          # add x10, x10, #0x708 (&sta_ops.address)
early_attach[0x52e0e4] = 0x79401a69                          # ldrh w9, [x19, #12]
early_attach[0x52e0e8] = 0xb9000148                          # str w8, [x10]
early_attach[0x52e0ec] = 0x79000949                          # strh w9, [x10, #4]
early_attach[0x52e0f0] = 0xaa1303e0                          # mov x0, x19
early_attach[0x52e0f4] = encode_bl(0x52e0f4, 0x52b300)      # bl redwood_net_attach
early_attach[0x52e0f8] = encode_cbz(0x52e0f8, 0x52e10c, 0)   # cbz w0, 0x52e10c (skip sta_attach if net_attach fails)
early_attach[0x52e0fc] = encode_adrp(0x52e0fc, 0xc21000, 0)  # adrp x0, 0xc21000
early_attach[0x52e100] = 0x911b4000                          # add x0, x0, #0x6d0 (&sta_ops)
early_attach[0x52e104] = encode_bl(0x52e104, 0x529d20)      # bl redwood_sta_attach
early_attach[0x52e108] = 0xd503201f                          # nop
early_attach[0x52e10c] = encode_bl(0x52e10c, 0xb033e0)      # bl MiniIONetworkStackStart
early_attach[0x52e110] = 0xa9417bfd                          # ldp x29, x30, [sp, #16]
early_attach[0x52e114] = 0xa8c24ff4                          # ldp x20, x19, [sp], #32
early_attach[0x52e118] = 0xd65f03c0                          # ret

# Pad to 0x52e130 with NOPs
for a in range(0x52e11c, 0x52e130, 4):
    early_attach[a] = 0xd503201f

for addr, insn in early_attach.items():
    struct.pack_into('<I', data, addr, insn)

with open('xnu/out/kernel.development.sweet', 'wb') as f:
    f.write(data)

print("kernel.development.sweet successfully generated with exact branch targets!")
