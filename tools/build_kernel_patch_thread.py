import struct, os, sys

def encode_b(pc, target):
    delta = (target - pc) // 4
    return 0x14000000 | (delta & 0x3ffffff)

def encode_bl(pc, target):
    delta = (target - pc) // 4
    return 0x94000000 | (delta & 0x3ffffff)

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

def encode_cbnz(pc, target, rt):
    delta = (target - pc) // 4
    return 0x35000000 | ((delta & 0x7ffff) << 5) | rt

with open('xnu/out/kernel.development.sweet.orig', 'rb') as f:
    data = bytearray(f.read())

# 1. IOEthernetInterface string and en0 string
str_bytes = b'IOEthernetInterface\x00en0\x00\x00'
data[0x156e5b : 0x156e5b + len(str_bytes)] = str_bytes

# 2. RedwoodWLAN publish("en0") at 0xb02b38
# add x1, x1, #0xe6f ("en0")
struct.pack_into('<I', data, 0xb02b38, 0x9139bc21)

# Function addresses
# 0x52e030: topaz_sta_init
# 0x52e074: sta_ready
# 0x52e0ac: sta_bring_up
# 0x52e0c8: sta_attach_thread
# 0x52e130: sta_rx
# 0x52e140: sta_link_changed

insns = {}

# 0x52e030: topaz_sta_init
insns[0x52e030] = 0xd10083ff # sub sp, sp, #0x20
insns[0x52e034] = 0xa9017bfd # stp x29, x30, [sp, #16]
insns[0x52e038] = 0x910043fd # add x29, sp, #0x10
insns[0x52e03c] = encode_adrp(0x52e03c, 0xcdc000, 8) # adrp x8, 0xcdc000
insns[0x52e040] = encode_adr(0x52e040, 0x52e074, 9)   # adr x9, sta_ready (0x52e074)
insns[0x52e044] = 0xf9079109 # str x9, [x8, #3872] (topaz_wlan_ready_hook = sta_ready)
insns[0x52e048] = encode_adr(0x52e048, 0x52e0c8, 0)   # adr x0, sta_attach_thread (0x52e0c8)
insns[0x52e04c] = 0xaa1f03e1 # mov x1, xzr
insns[0x52e050] = 0x910023e2 # add x2, sp, #8
insns[0x52e054] = 0xf90007ff # str xzr, [sp, #8]
insns[0x52e058] = encode_bl(0x52e058, 0x3a3be0)      # bl kernel_thread_start
insns[0x52e05c] = encode_cbnz(0x52e05c, 0x52e068, 0) # cbnz w0, 0x52e068
insns[0x52e060] = 0xf94007e0 # ldr x0, [sp, #8]
insns[0x52e064] = encode_bl(0x52e064, 0x3a1e50)      # bl thread_deallocate
insns[0x52e068] = 0xa9417bfd # ldp x29, x30, [sp, #16]
insns[0x52e06c] = 0x910083ff # add sp, sp, #0x20
insns[0x52e070] = 0xd65f03c0 # ret

# 0x52e074: sta_ready
insns[0x52e074] = 0xd10083ff # sub sp, sp, #0x20
insns[0x52e078] = 0xa9017bfd # stp x29, x30, [sp, #16]
insns[0x52e07c] = 0x910043fd # add x29, sp, #0x10
insns[0x52e080] = encode_adr(0x52e080, 0x52e0ac, 0)   # adr x0, sta_bring_up (0x52e0ac)
insns[0x52e084] = 0xaa1f03e1 # mov x1, xzr
insns[0x52e088] = 0x910023e2 # add x2, sp, #8
insns[0x52e08c] = 0xf90007ff # str xzr, [sp, #8]
insns[0x52e090] = encode_bl(0x52e090, 0x3a3be0)      # bl kernel_thread_start
insns[0x52e094] = encode_cbnz(0x52e094, 0x52e0a0, 0) # cbnz w0, 0x52e0a0
insns[0x52e098] = 0xf94007e0 # ldr x0, [sp, #8]
insns[0x52e09c] = encode_bl(0x52e09c, 0x3a1e50)      # bl thread_deallocate
insns[0x52e0a0] = 0xa9417bfd # ldp x29, x30, [sp, #16]
insns[0x52e0a4] = 0x910083ff # add sp, sp, #0x20
insns[0x52e0a8] = 0xd65f03c0 # ret

# 0x52e0ac: sta_bring_up
insns[0x52e0ac] = encode_adrp(0x52e0ac, 0xcdc000, 11) # adrp x11, 0xcdc000
insns[0x52e0b0] = encode_adr(0x52e0b0, 0x52e130, 9)   # adr x9, sta_rx (0x52e130)
insns[0x52e0b4] = 0xf9079569                          # str x9, [x11, #3880] (topaz_wlan_rx_hook)
insns[0x52e0b8] = encode_adr(0x52e0b8, 0x52e140, 9)   # adr x9, sta_link_changed (0x52e140)
insns[0x52e0bc] = 0xf9079969                          # str x9, [x11, #3888] (topaz_wlan_link_hook)
insns[0x52e0c0] = encode_bl(0x52e0c0, 0x4ca7c0)       # bl current_thread
insns[0x52e0c4] = encode_b(0x52e0c4, 0x3a6390)        # b thread_terminate

# 0x52e0c8: sta_attach_thread
insns[0x52e0c8] = 0xa9be4ff4 # stp x20, x19, [sp, #-32]!
insns[0x52e0cc] = 0xa9017bfd # stp x29, x30, [sp, #16]
insns[0x52e0d0] = 0x910043fd # add x29, sp, #0x10
insns[0x52e0d4] = 0x52803e80 # mov w0, #500 (IOSleep 500ms)
insns[0x52e0d8] = encode_bl(0x52e0d8, 0xa23210)       # bl IOSleep
insns[0x52e0dc] = encode_adrp(0x52e0dc, 0xc21000, 19) # adrp x19, 0xc21000
insns[0x52e0e0] = 0x911ac273                          # add x19, x19, #0x6b0 (&sta_link)
insns[0x52e0e4] = 0x91002260                          # add x0, x19, #8 (sta_link.address)
insns[0x52e0e8] = encode_bl(0x52e0e8, 0xae84e0)       # bl topaz_wlan_address
insns[0x52e0ec] = 0xb9400a68                          # ldr w8, [x19, #8]
insns[0x52e0f0] = encode_adrp(0x52e0f0, 0xc21000, 10) # adrp x10, 0xc21000
insns[0x52e0f4] = 0x911c214a                          # add x10, x10, #0x708 (&sta_ops.address)
insns[0x52e0f8] = 0x79401a69                          # ldrh w9, [x19, #12]
insns[0x52e0fc] = 0xb9000148                          # str w8, [x10]
insns[0x52e100] = 0x79000949                          # strh w9, [x10, #4]
insns[0x52e104] = 0xaa1303e0                          # mov x0, x19
insns[0x52e108] = encode_bl(0x52e108, 0x52b300)       # bl redwood_net_attach
insns[0x52e10c] = encode_cbz(0x52e10c, 0x52e11c, 0)   # cbz w0, 0x52e11c
insns[0x52e110] = encode_adrp(0x52e110, 0xc21000, 0)  # adrp x0, 0xc21000
insns[0x52e114] = 0x911b4000                          # add x0, x0, #0x6d0 (&sta_ops)
insns[0x52e118] = encode_bl(0x52e118, 0x529d20)       # bl redwood_sta_attach
insns[0x52e11c] = encode_bl(0x52e11c, 0xb033e0)       # bl MiniIONetworkStackStart
insns[0x52e120] = encode_bl(0x52e120, 0x4ca7c0)       # bl current_thread
insns[0x52e124] = 0xa9417bfd                          # ldp x29, x30, [sp, #16]
insns[0x52e128] = 0xa8c24ff4                          # ldp x20, x19, [sp], #32
insns[0x52e12c] = encode_b(0x52e12c, 0x3a6390)        # b thread_terminate

for addr, insn in insns.items():
    struct.pack_into('<I', data, addr, insn)

out_path = 'xnu/out/kernel.development.sweet'
with open(out_path, 'wb') as f:
    f.write(data)

print(f"Successfully generated {out_path} ({len(data)} bytes)")
