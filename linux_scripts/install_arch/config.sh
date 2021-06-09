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

cat << '!EOF!' >> /etc/pacman.conf
[archlinuxcn]
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinuxcn/$arch
!EOF!
pacman -Syuu
pacman -S archlinuxcn-keyring --noconfirm
pacman -S archlinuxcn-mirrorlist-git clash-geoip clash-premium-bin nmap socat grub openssh python python-pip zsh zsh-doc tcpdump man git zip unzip wget cronie bmon vim networkmanager fail2ban nginx mariadb netdata --noconfirm
curl https://cdn.jsdelivr.net/gh/d-w-x/files_and_scripts@master/linux_scripts/install_arch/files/clash.service -o /etc/systemd/system/clash@.service
curl https://cdn.jsdelivr.net/gh/d-w-x/files_and_scripts@master/linux_scripts/install_arch/files/renew_log.sh -o /root/renew_log.sh
curl https://cdn.jsdelivr.net/gh/d-w-x/files_and_scripts@master/linux_scripts/install_arch/files/fail2ban.tgz -o /etc/fail2ban/fail2ban.tgz
cd /etc/fail2ban
tar -zxvf fail2ban.tgz

systemctl disable systemd-networkd.service systemd-resolved.service
systemctl enable NetworkManager.service sshd.service cronie.service he-ipv6.service nginx.service mariadb.service
ssh-keygen -b 4096
sh -c "$(curl -fsSL https://cdn.jsdelivr.net/gh/ohmyzsh/ohmyzsh@master/tools/install.sh)"
sed "s/robbyrussell/random/g" /root/.zshrc -i
sed "s/(git)/(git zsh-autosuggestions zsh-syntax-highlighting z extract command-not-found colored-man-pages colorize)/" /root/.zshrc -i
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

mkdir /etc/cert
curl https://get.acme.sh | sh
mkdir -p /var/www/letsencrypt

chown -R netdata /usr/share/netdata/web
ln -s /bin/vim /bin/vi
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
