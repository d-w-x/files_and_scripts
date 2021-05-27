#/bin/env bash
echo "============================================"
echo "================Update System==============="
echo "============================================"
apt update && apt upgrade -y

echo "============================================"
echo "==============Getting bootstrap============="
echo "============================================"
cd /tmp
site=$(cat /etc/apt/sources.list |grep "^deb" |head -n 1 | awk '{print $2}'| awk -F/ '{ print $3 }')
date=$( date "+%Y.%m.01" )
wget http://${site}/archlinux/iso/${date}/archlinux-bootstrap-${date}-x86_64.tar.gz
tar xzvf archlinux-bootstrap-${date}-x86_64.tar.gz
mount --bind /tmp/root.x86_64 /tmp/root.x86_64

mv /tmp/root.x86_64/etc/pacman.d/mirrorlist /tmp/root.x86_64/etc/pacman.d/mirrorlist.back
echo "Server = http://${site}"'/archlinux/$repo/os/$arch' >> /tmp/root.x86_64/etc/pacman.d/mirrorlist

echo "============================================"
echo "============Switch to bootstrap============="
echo "============================================"
/tmp/root.x86_64/bin/arch-chroot /tmp/root.x86_64/ # 有报错
