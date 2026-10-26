def update_0026():
    patch_path = 'xnu/patches/0026-sweet-builtin-hfs.patch'
    with open(patch_path, 'r', encoding='utf-8') as f:
        content = f.read()

    file_diffs = content.split('diff --git ')
    new_file_diffs = [file_diffs[0]]

    for fd in file_diffs[1:]:
        header_line = fd.split('\n')[0]
        file_name = header_line.split(' ')[0]

        if 'bsd/sweet_hfs/sweet_hfs_iokit.c' in file_name:
            # Add includes & sweet_hfs_vfs_getattr
            target_includes = (
                "+#include \"hfs_iokit.h\"\n"
                "+#include \"hfs_encodings/hfs_encodings_internal.h\""
            )
            repl_includes = (
                "+#include \"hfs_iokit.h\"\n"
                "+#include \"hfs_encodings/hfs_encodings_internal.h\"\n"
                "+#include <sys/attr.h>\n"
                "+#include <sys/mount.h>\n"
                "+\n"
                "+extern int hfs_statfs(struct mount *mp, struct vfs_statfs *sbp, vfs_context_t context);\n"
                "+\n"
                "+static int\n"
                "+sweet_hfs_vfs_getattr(mount_t mp, struct vfs_attr *vfa, vfs_context_t ctx)\n"
                "+{\n"
                "+\tstruct vfs_statfs sfs;\n"
                "+\tint error;\n"
                "+\n"
                "+\terror = hfs_statfs(mp, &sfs, ctx);\n"
                "+\tif (error) {\n"
                "+\t\treturn error;\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_blocks)) {\n"
                "+\t\tvfa->f_blocks = sfs.f_blocks;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_blocks);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bsize)) {\n"
                "+\t\tvfa->f_bsize = sfs.f_bsize;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bsize);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bfree)) {\n"
                "+\t\tvfa->f_bfree = sfs.f_bfree;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bfree);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bavail)) {\n"
                "+\t\tvfa->f_bavail = sfs.f_bavail;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bavail);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bused)) {\n"
                "+\t\tvfa->f_bused = sfs.f_blocks - sfs.f_bfree;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bused);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_files)) {\n"
                "+\t\tvfa->f_files = sfs.f_files;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_files);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_ffree)) {\n"
                "+\t\tvfa->f_ffree = sfs.f_ffree;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_ffree);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_fsid)) {\n"
                "+\t\tvfa->f_fsid = sfs.f_fsid;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_fsid);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_capabilities)) {\n"
                "+\t\tvfa->f_capabilities.capabilities[VOL_CAPABILITIES_FORMAT] =\n"
                "+\t\t    VOL_CAP_FMT_PERSISTENTOBJECTIDS | VOL_CAP_FMT_SYMBOLICLINKS |\n"
                "+\t\t    VOL_CAP_FMT_HARDLINKS | VOL_CAP_FMT_JOURNALED;\n"
                "+\t\tvfa->f_capabilities.valid[VOL_CAPABILITIES_FORMAT] = 0xffffffff;\n"
                "+\t\tvfa->f_capabilities.capabilities[VOL_CAPABILITIES_INTERFACES] =\n"
                "+\t\t    VOL_CAP_INT_SEARCHFS | VOL_CAP_INT_ATTRLIST | VOL_CAP_INT_READDIRATTR;\n"
                "+\t\tvfa->f_capabilities.valid[VOL_CAPABILITIES_INTERFACES] = 0xffffffff;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_capabilities);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_attributes)) {\n"
                "+\t\tvfa->f_attributes.valid[VOL_CAPABILITIES_FORMAT] = 0xffffffff;\n"
                "+\t\tvfa->f_attributes.valid[VOL_CAPABILITIES_INTERFACES] = 0xffffffff;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_attributes);\n"
                "+\t}\n"
                "+\treturn 0;\n"
                "+}"
            )
            assert target_includes in fd, "target_includes not found in sweet_hfs_iokit.c"
            fd = fd.replace(target_includes, repl_includes, 1)

            # Assign hfs_vfsops.vfs_getattr
            target_fsadd = "+\tint ret = vfs_fsadd(&vfe, &sweet_hfs_vfs_handle);"
            repl_fsadd = (
                "+\thfs_vfsops.vfs_getattr = sweet_hfs_vfs_getattr;\n"
                "+\tint ret = vfs_fsadd(&vfe, &sweet_hfs_vfs_handle);"
            )
            assert target_fsadd in fd, "target_fsadd not found in sweet_hfs_iokit.c"
            fd = fd.replace(target_fsadd, repl_fsadd, 1)

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

    print("Successfully updated patch 0026!")

if __name__ == '__main__':
    update_0026()
