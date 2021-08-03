#/bin/env bash
echo "============================================"
echo "===============Configing Arch==============="
echo "============================================"

echo "==locale=="
sed "s/#en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/" /etc/locale.gen -i
echo 'LANG=en_US.UTF-8'>> /etc/locale.conf
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
locale-gen

echo "==hosts=="
read -p "Enter your hostname:" hostnm
echo "$hostnm" >> /etc/hostname
cat << !EOF! >> /etc/hosts
127.0.0.1    localhost
127.0.0.1    ${hostnm}
::1          localhost ip6-localhost ip6-loopback
ff02::1      ip6-allnodes
ff02::2      ip6-allrouters
!EOF!

echo "==he-ipv6=="
netdevice=$(ip link |grep UP |grep -v LOOPBACK |head -n 1 |awk '{print $2}' |sed 's/://')
ipaddr=$(ip a |grep "inet " |grep -v " lo$" |awk '{print $2}' |sed 's#/..##')
read -p "Install he-ipv6? :(y/n) " he
case $he in
    [yY][eE][sS]|[yY])
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
		;;
    *)
		echo "No he-ipv6!"
		exit 1
		;;
esac
echo "==.gitconfig=="
cat << !EOF! > /root/.gitconfig
[pull]
	rebase = false
[init]
	defaultBranch = master
[url "https://ghproxy.com/https://github.com"]
	insteadOf = https://github.com
!EOF!

echo "==software=="
cat << '!EOF!' >> /etc/pacman.conf
[archlinuxcn]
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinuxcn/$arch
!EOF!

mv /etc/resolv.conf.back /etc/resolv.conf
sed "s/#ParallelDownloads = 5/ParallelDownloads = 5/g" /etc/pacman.conf -i
pacman -Syuu
pacman -S archlinuxcn-keyring --noconfirm
pacman -S archlinuxcn-mirrorlist-git clash-geoip clash-premium-bin nmap socat grub openssh python python-pip zsh zsh-doc tcpdump man git zip unzip wget cronie bmon vim networkmanager fail2ban nginx mariadb --noconfirm
curl https://cdn.jsdelivr.net/gh/d-w-x/files_and_scripts@master/linux_scripts/install_arch/files/clash.service -o /etc/systemd/system/clash@.service
curl https://cdn.jsdelivr.net/gh/d-w-x/files_and_scripts@master/linux_scripts/install_arch/files/renew_log.sh -o /root/renew_log.sh
curl https://cdn.jsdelivr.net/gh/d-w-x/files_and_scripts@master/linux_scripts/install_arch/files/fail2ban.tgz -o /etc/fail2ban/fail2ban.tgz
curl https://cdn.jsdelivr.net/gh/d-w-x/files_and_scripts@master/linux_scripts/install_arch/files/nginx_renew.sh -o /etc/nginx/nginx_renew.sh
tar -zxvf /etc/fail2ban/fail2ban.tgz -C /etc/fail2ban
rm -rf /etc/fail2ban/fail2ban.tgz

echo "==systemctl=="
systemctl disable systemd-networkd.service systemd-resolved.service
systemctl enable NetworkManager.service sshd.service cronie.service he-ipv6.service nginx.service mariadb.service iptables.service fail2ban.service
ssh-keygen -b 4096

echo "==sshd=="
sed "s/#TCPKeepAlive yes/TCPKeepAlive yes/g" /etc/ssh/sshd_config -i
sed "s/#ClientAliveInterval 0/ClientAliveInterval 30/g" /etc/ssh/sshd_config -i
sed "s/#ClientAliveCountMax 3/ClientAliveCountMax 3/g" /etc/ssh/sshd_config -i

echo "==zsh=="
sh -c "$(curl -fsSL https://cdn.jsdelivr.net/gh/ohmyzsh/ohmyzsh@master/tools/install.sh)"
sed "s/robbyrussell/random/g" /root/.zshrc -i
sed "s/(git)/(git zsh-autosuggestions zsh-syntax-highlighting z extract command-not-found colored-man-pages colorize)/" /root/.zshrc -i
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

echo "==acme=="
mkdir /etc/cert
curl https://get.acme.sh | sh
mkdir -p /var/www/letsencrypt

echo "==bbr=="
touch /etc/sysctl.conf
mkdir -p /etc/sysctl.d
cat << '!EOF!' >> /etc/sysctl.d/99-bbr.conf
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_syncookies = 1
#net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_max_tw_buckets = 5000
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
!EOF!

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