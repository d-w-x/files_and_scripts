#/bin/env bash
echo "============================================"
echo "===============Configing Arch==============="
echo "============================================"
sed "s/#en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/" /etc/locale.gen -i
locale-gen
echo 'LANG=en_US.UTF-8'>> /etc/locale.conf
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
hwclock --systohc
read -p "Enter your hostname:" hostnm
echo "$hostnm" >> /etc/hostname
cat << !EOF! >> /etc/hosts
127.0.0.1    localhost
127.0.0.1    ${hostnm}

::1          localhost ip6-localhost ip6-loopback
ff02::1      ip6-allnodes
ff02::2      ip6-allrouters
!EOF!

netdevice=$(ip link |grep UP |grep -v LOOPBACK |head -n 1 |awk '{print $2}' |sed 's/://')
# ipaddr=$(ip a |grep "inet " |grep -v " lo$" |awk '{print $2}' |sed 's#/..##')
systemctl disable systemd-networkd.service systemd-resolved.service
systemctl enable NetworkManager.service sshd.service cronie.service
passwd

echo "============================================"
echo "=================Gen Start=================="
echo "============================================"
mkinitcpio -P
device=$( df -h |grep '/$' |awk '{print $1}')
device=${device:0:8}
grub-install $device
grub-mkconfig -o /boot/grub/grub.cfg
read -p "Is grub install correct:(y/n) " corr
case $corr in
    [yY][eE][sS]|[yY])
		echo "Install done, hard reboot please."
		;;
    *)
		echo "Exitting...Try rerun 'mkinitcpio -P && grub-install [your_disk] && grub-mkconfig -o /boot/grub/grub.cfg'"
		exit 1
		;;
esac
