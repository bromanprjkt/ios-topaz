#!/usr/bin/env python3
"""Apply the SWEET bring-up changes to an iOS root made by tools/mkiosroot.sh.

  sudo sweet-root-tweaks.py MOUNTED_ROOT

MOUNTED_ROOT is the HFS+ image mounted read-write (Linux: run
`fsck.hfsplus -fy` on the image, then `mount -t hfsplus -o loop,force`).
Run as root (it writes root/mobile owned files). Idempotent. This is what
turned the plain mkiosroot.sh output into the images that reach the home
screen (image versions v8-v14 in NOTES.md):

  launchd.plist   _PanicOnCrash -> _PanicOnCrasX (a crashing daemon must not
                  panic the system); CommCenter jobs removed (no baseband: it
                  crash-loops and Setup blocks on its CoreTelephony XPC)
  containers      /private/var/containers/{Bundle,Data/System,Shared/SystemGroup,Temp}
                  (on iOS they live on the data volume)
  migration       LastSystemVersion so DataMigration does not run for an hou
                  on every boot
  audio           VirtualAudio HAL plug-in disabled (mediaserverd crash)
  MediaToolbox    StartRecorderServer=false (camera filter prewarm calls a
                  NULL OpenGL function without a GPU -> mediaserverd crash loop)
  SpringBoard     BKNoWatchdogs (one slow CPU path, no scene-create watchdog
                  kills), no cloud-configuration UI
  Setup           skipped: SetupDone, SetupFinishedAllSteps, SetupVersion 11,
                  mini-buddy flags off
  activation      mobileactivationd data ark seeded; the actual Activated state
                  comes from its Hactivation branch, selected by the /chosen
                  security-status properties in tools/mkadt.py
"""
import glob, os, plistlib, shutil, sys

BUILD, VERSION = '20H392', '16.7.16'
MOBILE = 501


def load(path):
    with open(path, 'rb') as f:
        return plistlib.load(f)


def save(path, data, uid, gid, mode, fmt=plistlib.FMT_BINARY):
    with open(path, 'wb') as f:
        plistlib.dump(data, f, fmt=fmt)
    os.chown(path, uid, gid)
    os.chmod(path, mode)


def merge_pref(root, name, values):
    """Merge keys into /var/mobile/Library/Preferences/NAME.plist (mobile, 0600)."""
    path = os.path.join(root, 'private/var/mobile/Library/Preferences', name + '.plist')
    data = load(path) if os.path.exists(path) else {}
    data.update(values)
    save(path, data, MOBILE, MOBILE, 0o600)
    print('pref', name, sorted(values))


def launchd(root):
    path = os.path.join(root, 'System/Library/xpc/launchd.plist')
    st = os.stat(path)
    plist = load(path)
    jobs = plist['LaunchDaemons']
    renamed = 0
    for job in jobs.values():
        if '_PanicOnCrash' in job:
            job['_PanicOnCrasX'] = job.pop('_PanicOnCrash')
            renamed += 1
    removed = [k for k, j in jobs.items() if j.get('Label') == 'com.apple.CommCenter']
    for k in removed:
        del jobs[k]
    save(path, plist, st.st_uid, st.st_gid, st.st_mode & 0o7777)
    print(f'launchd.plist: {renamed} _PanicOnCrash renamed, {len(removed)} CommCenter jobs removed')


def containers(root):
    base = os.path.join(root, 'private/var/containers')
    for sub, uid in (('Bundle', 33), ('Data/System', 0), ('Shared/SystemGroup', 0), ('Temp', 0)):
        d = os.path.join(base, sub)
        if not os.path.isdir(d):
            os.makedirs(d)
            os.chown(d, uid, uid)
            os.chmod(d, 0o755)
            print('mkdir', d)

    sg_base = os.path.join(base, 'Shared/SystemGroup')
    for group_id in (
        'systemgroup.com.apple.lsd',
        'systemgroup.com.apple.lsd.iconscache',
        'systemgroup.com.apple.mobilegestaltcache',
        'systemgroup.com.apple.installcoordinationd',
    ):
        grp_dir = os.path.join(sg_base, group_id)
        for sub_dir in ('', 'Library', 'Library/Caches', 'Library/Preferences'):
            p = os.path.join(grp_dir, sub_dir)
            os.makedirs(p, exist_ok=True)
            os.chown(p, MOBILE, MOBILE)
            os.chmod(p, 0o777)
        meta_file = os.path.join(grp_dir, '.com.apple.mobile_container_manager.metadata.plist')
        if not os.path.exists(meta_file):
            save(meta_file, {
                'MCMMetadataIdentifier': group_id,
                'MCMMetadataUUID': group_id,
            }, 0, 0, 0o644)
            print('seeded container', group_id)


def mobilegestalt(root):
    import base64, hashlib
    def mg_key(name):
        h = hashlib.md5(('MGCopyAnswer' + name).encode()).digest()
        return base64.b64encode(h).decode().rstrip('=')

    mg_cache_dir = os.path.join(root, 'private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches')
    os.makedirs(mg_cache_dir, exist_ok=True)
    os.chown(mg_cache_dir, MOBILE, MOBILE)
    os.chmod(mg_cache_dir, 0o777)

    cache_path = os.path.join(mg_cache_dir, 'com.apple.MobileGestalt.plist')
    extra = {
        mg_key('ProductType'): 'iPhone10,3',
        mg_key('HWModelStr'): 'D22AP',
        mg_key('DeviceClass'): 'iPhone',
        mg_key('BuildVersion'): BUILD,
        mg_key('ProductVersion'): VERSION,
        mg_key('HasHomeButton'): False,
        mg_key('HomeButtonType'): 2,
        mg_key('MainScreenScale'): 3.0,
        mg_key('MainScreenPitch'): 458.0,
        mg_key('ArtworkTraits'): {
            'ArtworkScaleFactor': 3,
            'ArtworkDeviceDisplayGamut': 0,
            'ArtworkDeviceIdiom': 'phone',
            'ArtworkDeviceSubtype': 2436,
        },
    }
    payload = {
        'CacheUUID': '87066E3A-4442-11F1-A14D-F16241AA8750',
        'CacheVersion': 1,
        '_kCFSystemVersionBuildVersionKey': BUILD,
        '_kCFSystemVersionProductVersionKey': VERSION,
        'CacheExtra': extra,
        'CacheData': b'',
    }
    save(cache_path, payload, MOBILE, MOBILE, 0o644)
    print('seeded MobileGestalt cache at', cache_path)

    # Also seed in fallback locations
    for fb_dir in [
        os.path.join(root, 'private/var/mobile/Library/Caches'),
        os.path.join(root, 'private/var/mobile/Library/Preferences')
    ]:
        os.makedirs(fb_dir, exist_ok=True)
        save(os.path.join(fb_dir, 'com.apple.MobileGestalt.plist'), payload, MOBILE, MOBILE, 0o644)


def find_container(root, kind, identifier):
    for meta in glob.glob(os.path.join(root, 'private/var/containers', kind, '*',
                                       '.com.apple.mobile_container_manager.metadata.plist')):
        if load(meta).get('MCMMetadataIdentifier') == identifier:
            return os.path.dirname(meta)
    return None


def activation(root):
    c = find_container(root, 'Data/System', 'com.apple.mobileactivationd')
    if c is None:
        c = os.path.join(root, 'private/var/containers/Data/System/D90C94C4-F94E-4FCF-8A28-A93BE3846D8E')
        os.makedirs(c, exist_ok=True)
        os.chown(c, 0, 0)
        os.chmod(c, 0o755)
        save(os.path.join(c, '.com.apple.mobile_container_manager.metadata.plist'), {
            'MCMMetadataIdentifier': 'com.apple.mobileactivationd',
            'MCMMetadataUUID': 'D90C94C4-F94E-4FCF-8A28-A93BE3846D8E',
        }, 0, 0, 0o644)
    d = os.path.join(c, 'Library/internal')
    os.makedirs(d, exist_ok=True)
    os.chown(d, MOBILE, MOBILE)
    os.chmod(d, 0o755)
    save(os.path.join(d, 'data_ark.plist'), {
        '-ActivationState': 'Activated', '-BrickState': False,
        '-BuildVersion': BUILD, '-ProductVersion': VERSION,
        '-DataMigrationCompleted': True, '-PreSydroDataMigrationCompleted': True,
    }, MOBILE, MOBILE, 0o600)
    print('data ark seeded in', d)


def audio(root):
    src = os.path.join(root, 'Library/Audio/Plug-Ins/HAL/VirtualAudio.plugin')
    dst_dir = os.path.join(root, 'Library/Audio/Plug-Ins/HAL.disabled')
    if os.path.exists(src):
        os.makedirs(dst_dir, exist_ok=True)
        shutil.move(src, dst_dir)
        print('VirtualAudio.plugin disabled')
    for conf in glob.glob(os.path.join(root, 'System/Library/Frameworks/MediaToolbox.framework/*/SubServerConfiguration.plist')):
        st = os.stat(conf)
        data = load(conf)
        data['StartRecorderServer'] = False
        save(conf, data, st.st_uid, st.st_gid, st.st_mode & 0o7777, plistlib.FMT_XML)
        print('StartRecorderServer off', os.path.relpath(conf, root))


def migration(root):
    uuids = [
        'A9683613-3704-53F2-95D0-98A8FB574E78',
        'a9683613-3704-53f2-95d0-98a8fb574e78',
        '5C527BDD-C4EC-5214-B301-D92BAFAB8D31',
        '5c527bdd-c4ec-5214-b301-d92bafab8d31',
    ]
    mig_payload = {
        'LastSystemVersion': BUILD,
        'DMUserDataDisposition': {'SyntheticDidUpgrade': False, 'buildVersion': BUILD}
    }
    dm_payload = {'LastSystemVersion': BUILD}

    for user_dir, uid in [('private/var/mobile', MOBILE), ('private/var/root', 0)]:
        pref_dir = os.path.join(root, user_dir, 'Library/Preferences')
        byhost_dir = os.path.join(pref_dir, 'ByHost')
        os.makedirs(byhost_dir, exist_ok=True)
        os.chown(byhost_dir, uid, uid)
        os.chmod(byhost_dir, 0o755)

        save(os.path.join(pref_dir, 'com.apple.migration.plist'), mig_payload, uid, uid, 0o600)
        save(os.path.join(pref_dir, 'com.apple.DataMigration.plist'), dm_payload, uid, uid, 0o600)

        for u in uuids:
            save(os.path.join(byhost_dir, f'com.apple.migration.{u}.plist'), mig_payload, uid, uid, 0o600)
            save(os.path.join(byhost_dir, f'com.apple.DataMigration.{u}.plist'), dm_payload, uid, uid, 0o600)

    sentinel = os.path.join(root, 'private/var/datamigrator/migrate')
    if os.path.exists(sentinel):
        os.remove(sentinel)
        print('removed migration sentinel')
    print('migration preferences and ByHost populated')


def main():
    if len(sys.argv) != 2 or not os.path.isdir(os.path.join(sys.argv[1], 'System/Library/xpc')):
        sys.exit(__doc__)
    root = sys.argv[1]
    launchd(root)
    containers(root)
    mobilegestalt(root)
    activation(root)
    audio(root)
    migration(root)
    merge_pref(root, 'com.apple.springboard', {
        'BKNoWatchdogs': True,
        'FBLaunchWatchdogExceptions': {'com.apple.purplebuddy': 100.0},
        'MCForceShowCloudConfigurationUI': False})
    merge_pref(root, 'com.apple.purplebuddy', {
        'SetupDone': True, 'SetupFinishedAllSteps': True, 'SetupVersion': 11,
        'daemonizeNeedsToRun': False})
    merge_pref(root, 'com.apple.purplebuddy.notbackedup', {
        k: False for k in ('ShouldRunDiagnosticsMiniBuddy', 'ShouldRunHSA2MiniBuddy',
                           'ShouldRunKeychainSyncMiniBuddy', 'ShouldRunMesaMiniBuddy',
                           'ShouldRunPaymentMiniBuddy', 'ShouldRunStandardMiniBuddy',
                           'SilentICDPUpgrade')})
    merge_pref(root, 'com.apple.managedconfiguration.notbackedup', {
        'LockdownActivationIndicatesCloudConfigurationAvailable': False})


if __name__ == '__main__':
    main()
