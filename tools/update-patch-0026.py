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
            # We want to replace sweet_hfs_vfs_getattr implementation with the clean one using struct vfsstatfs
            # First find where includes are
            old_block_start = "+#include \"hfs_iokit.h\"\n+#include \"hfs_encodings/hfs_encodings_internal.h\""
            
            # Find everything from old_block_start to "+#ifndef panic_on_assert"
            idx_start = fd.find(old_block_start)
            idx_end = fd.find("+#ifndef panic_on_assert", idx_start)
            assert idx_start != -1 and idx_end != -1, "Could not find insertion region in sweet_hfs_iokit.c"

            clean_block = (
                "+#include \"hfs_iokit.h\"\n"
                "+#include \"hfs_encodings/hfs_encodings_internal.h\"\n"
                "+#include <sys/attr.h>\n"
                "+#include <sys/mount.h>\n"
                "+\n"
                "+static int\n"
                "+sweet_hfs_vfs_getattr(mount_t mp, struct vfs_attr *vfa, vfs_context_t ctx __unused)\n"
                "+{\n"
                "+\tstruct vfsstatfs *sfs = vfs_statfs(mp);\n"
                "+\tif (!sfs) {\n"
                "+\t\treturn EINVAL;\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_blocks)) {\n"
                "+\t\tvfa->f_blocks = sfs->f_blocks;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_blocks);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bsize)) {\n"
                "+\t\tvfa->f_bsize = sfs->f_bsize;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bsize);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bfree)) {\n"
                "+\t\tvfa->f_bfree = sfs->f_bfree;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bfree);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bavail)) {\n"
                "+\t\tvfa->f_bavail = sfs->f_bavail;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bavail);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_bused)) {\n"
                "+\t\tvfa->f_bused = sfs->f_blocks - sfs->f_bfree;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_bused);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_files)) {\n"
                "+\t\tvfa->f_files = sfs->f_files;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_files);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_ffree)) {\n"
                "+\t\tvfa->f_ffree = sfs->f_ffree;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_ffree);\n"
                "+\t}\n"
                "+\tif (VFSATTR_WANTED(vfa, f_fsid)) {\n"
                "+\t\tvfa->f_fsid = sfs->f_fsid;\n"
                "+\t\tVFSATTR_SET_SUPPORTED(vfa, f_fsid);\n"
                "+\t}\n"
                "+\treturn 0;\n"
                "+}\n"
                "+\n"
            )

            fd = fd[:idx_start] + clean_block + fd[idx_end:]

            # Make sure hfs_vfsops.vfs_getattr = sweet_hfs_vfs_getattr; is still there
            if "+\thfs_vfsops.vfs_getattr = sweet_hfs_vfs_getattr;" not in fd:
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

    print("Successfully updated patch 0026 with clean sweet_hfs_vfs_getattr!")

if __name__ == '__main__':
    update_0026()
