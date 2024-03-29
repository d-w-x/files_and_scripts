#!/bin/env bash
echo "============================================"
echo "=================Init  keys================="
echo "============================================"
pacman-key --init
pacman-key --populate archlinux
pacman -Syy
pacman -S vim grep sed --noconfirm

device=$(df -h |grep "/$" |awk '{print $1}')
mount $device /mnt
# 保留原始密钥
cat /mnt/home/ubuntu/.ssh/authorized_keys >> ~/authorized_keys
cat /mnt/root/.ssh/authorized_keys >> ~/authorized_keys
cd /mnt

echo "============================================"
echo "================Remove Files================"
echo "============================================"
read -r -p "Whether to continue? next step can't go back:(y/n)" input
case $input in
    [yY][eE][sS]|[yY])
		echo "Continuing..."
		;;
    *)
		echo "Exitting..."
		exit 1
		;;
esac
# 不可回退
ls |grep -v tmp |grep -v dev |grep -v proc |grep -v run |grep -v sys |xargs rm -rf {}

echo "============================================"
echo "=============Installing Arch================"
echo "============================================"
sed "s/#ParallelDownloads = 5/ParallelDownloads = 5/g" /etc/pacman.conf -i
pacstrap /mnt base base-devel linux linux-firmware linux-headers
genfstab -U /mnt >> /mnt/etc/fstab
cat /mnt/etc/fstab
mkdir /mnt/root/.ssh
cp ~/authorized_keys /mnt/root/.ssh/.

echo "============================================"
echo "============Switching to Arch==============="
echo "============================================"
rm /mnt/etc/resolv.conf
cp /etc/resolv.conf /mnt/etc/resolv.conf.back
arch-chroot /mnt # 此步骤不可有报错，可能由于 resolv.conf 引起
