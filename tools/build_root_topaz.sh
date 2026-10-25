#!/bin/bash
set -euo pipefail
cd /mnt/c/Users/pinkman/Documents/code/ios-topaz
rm -f /home/pinkman/ios16-root.img

echo "=== Step 1: Running mkiosroot.sh ==="
bash tools/mkiosroot.sh research/dmg/OS.dmg research/dmg/SystemOS.dmg research/dmg/AppOS.dmg /home/pinkman/ios16-root.img 16G

echo "=== Step 2: Mounting and running sweet-root-tweaks.py ==="
mkdir -p /mnt/iosroot
mount -t hfsplus -o loop,force /home/pinkman/ios16-root.img /mnt/iosroot
python3 tools/sweet-root-tweaks.py /mnt/iosroot
sync
umount /mnt/iosroot

echo "=== Step 3: Running fsck.hfsplus ==="
fsck.hfsplus -f -y /home/pinkman/ios16-root.img | grep -v "Illegal name" || true

echo "=== Step 4: Converting to sparse image (img2simg) ==="
rm -f ios16-root.simg
img2simg /home/pinkman/ios16-root.img ios16-root.simg

echo "=== Done! Generated ios16-root.simg ==="
ls -lh ios16-root.simg
