#/bin/env bash
echo "============================================"
echo "===============Configing Arch==============="
echo "============================================"
sed "s/#en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/" /etc/locale.gen -i
locale-gen
echo 'LANG=en_US.UTF-8'>> /etc/locale.conf
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
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
ipaddr=$(ip a |grep "inet " |grep -v " lo$" |awk '{print $2}' |sed 's#/..##')
read -p "Enter your he_ipv4:" he_ipv4
read -p "Enter your he_ipv6:" he_ipv6
cat << !EOF! > /etc/systemd/system/he-ipv6.service
[Unit]
Description=he.net IPv6 tunnel
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/ip tunnel add he-ipv6 mode sit remote ${he_ipv4} local ${ipaddr} ttl 255
ExecStart=/usr/bin/ip link set he-ipv6 up mtu 1480
ExecStart=/usr/bin/ip addr add ${he_ipv6} dev he-ipv6
ExecStart=/usr/bin/ip -6 route add ::/0 dev he-ipv6
ExecStop=/usr/bin/ip -6 route del ::/0 dev he-ipv6
ExecStop=/usr/bin/ip link set he-ipv6 down
ExecStop=/usr/bin/ip tunnel del he-ipv6

[Install]
WantedBy=multi-user.target
!EOF!

cat << !EOF! > /root/.gitconfig
[pull]
	rebase = false
[init]
	defaultBranch = master
[url "https://ghproxy.com/https://github.com"]
	insteadOf = https://github.com
!EOF!

systemctl disable systemd-networkd.service systemd-resolved.service
systemctl enable NetworkManager.service sshd.service cronie.service he-ipv6.service
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
