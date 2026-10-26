import ctypes, ctypes.wintypes, os, subprocess, sys

CRED_TYPE_GENERIC = 1
class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', ctypes.wintypes.DWORD),
        ('Type', ctypes.wintypes.DWORD),
        ('TargetName', ctypes.wintypes.LPWSTR),
        ('Comment', ctypes.wintypes.LPWSTR),
        ('LastWritten', ctypes.wintypes.FILETIME),
        ('CredentialBlobSize', ctypes.wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
        ('Persist', ctypes.wintypes.DWORD),
        ('AttributeCount', ctypes.wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', ctypes.wintypes.LPWSTR),
        ('UserName', ctypes.wintypes.LPWSTR),
    ]

advapi32 = ctypes.windll.advapi32
CredRead = advapi32.CredReadW
CredRead.argtypes = [ctypes.wintypes.LPWSTR, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
CredRead.restype = ctypes.wintypes.BOOL

pcred = ctypes.POINTER(CREDENTIAL)()
if not CredRead('git:https://github.com', CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
    print('Failed to read git credential', file=sys.stderr)
    sys.exit(1)

raw = ctypes.string_at(pcred.contents.CredentialBlob, pcred.contents.CredentialBlobSize)
token = raw.decode('utf-16-le') if b'\x00' in raw else raw.decode('utf-8')
token = token.strip('\x00\r\n ')

env = os.environ.copy()
env['GH_TOKEN'] = token

args = ['gh'] + sys.argv[1:]
res = subprocess.run(args, env=env)
sys.exit(res.returncode)
