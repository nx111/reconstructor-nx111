#!/bin/bash
list_remove_files(){
    cat <<EOF
        aisleriot
	firefox-locale-de
	firefox-locale-es
	firefox-locale-fr
	firefox-locale-it
	firefox-locale-pt
	firefox-locale-ru
	fonts-arphic-ukai
	fonts-arphic-uming
	gnome-mahjongg
	gnome-mines
	gnome-sudoku
	gnome-user-docs
	hunspell-de-at-frami
	hunspell-de-ch-frami
	hunspell-de-de-frami
	hunspell-en-au
	hunspell-en-ca
	hunspell-en-za
	hunspell-es
	hunspell-fr
	hunspell-fr-classical
	hunspell-it
	hunspell-pt-br
	hunspell-pt-pt
	hunspell-ru
	ibus-chewing
	ibus-hangul
	ibus-table-cangjie
	ibus-table-cangjie-big
	ibus-table-cangjie3
	ibus-table-cangjie5
	thunderbird-gnome-support
	libreoffice-l10n-en-za
	rhythmbox
	rhythmbox-data
	transmission-gtk
	thunderbird
	thunderbird-locale-en
	thunderbird-locale-en-us
	thunderbird-locale-zh-hans
	thunderbird-locale-de
	thunderbird-locale-en-gb
	thunderbird-locale-es-ar
	thunderbird-locale-es-es
	thunderbird-locale-es
	thunderbird-locale-fr
	thunderbird-locale-it
	thunderbird-locale-pt-br
	thunderbird-locale-pt-pt
	thunderbird-locale-pt
	thunderbird-locale-ru
	thunderbird-locale-zh-cn
	thunderbird-locale-zh-tw
	thunderbird-locale-zh-hant
	language-pack-de-base
	language-pack-gnome-es-base
	language-pack-es-base
	language-pack-gnome-fr-base
	language-pack-fr-base
	language-pack-gnome-it-base
	language-pack-gnome-pt-base
	language-pack-gnome-ru-base
	language-pack-it-base
	language-pack-pt-base
	language-pack-ru-base
	language-pack-gnome-de-base
	language-pack-gnome-es
	language-pack-es
	language-pack-gnome-fr
	language-pack-fr
	language-pack-gnome-it
	language-pack-gnome-pt
	language-pack-gnome-ru
	language-pack-it
	language-pack-pt
	language-pack-ru
	language-pack-gnome-de
	language-pack-de
	gnome-getting-started-docs-ru
	gnome-getting-started-docs-pt
	gnome-getting-started-docs-de
	gnome-getting-started-docs-es
	gnome-getting-started-docs-fr
	gnome-getting-started-docs-it
	gnome-user-docs-de
	gnome-user-docs-es
	gnome-user-docs-fr
	gnome-user-docs-it
	gnome-user-docs-pt
	gnome-user-docs-ru
	libreoffice-help-de
	libreoffice-help-en-gb
	libreoffice-help-en-us
	libreoffice-help-es
	libreoffice-help-fr
	libreoffice-help-it
	libreoffice-help-pt
	libreoffice-help-pt-br
	libreoffice-help-ru
	libreoffice-help-zh-tw
	gnome-getting-started-docs
EOF
}

list_install_files(){
cat << EOF
	aptitude-common
	aptitude
	apt-rdepends
	libcwidget4
	libxapian30
	unity-session
	ubuntu-unity-desktop
	lightdm
	unity-tweak-tool
	amd64-microcode
	intel-microcode
	cryptsetup
	at
	wine
	winetricks
	mono-complete
	compizconfig-settings-manager
	gstreamer1.0-libav
	gstreamer1.0-nice
	gstreamer1.0-plugins-bad
	gstreamer1.0-plugins-ugly
	cpufreqd
	indicator-applet-complete
	indicator-common
	indicator-datetime
	indicator-keyboard
	indicator-messages
	indicator-notifications
	indicator-power
	indicator-sensors
	indicator-session
	indicator-bluetooth
	indicator-cpufreq
	indicator-printers
	indicator-sound
	openjdk-11-jdk
	gawk
	brasero
	cmake
	gimp
	gucharmap
	dconf-editor
	gconf-editor
	gettext
	gnome-tweak-tool
	xterm
	refind
	curl
	axel
	p7zip
	rar
	unar
	gitk
	git-gui
	wimtools
	exfat-fuse
	exfat-utils
	f2fs-tools
	add-apt-key
	checkinstall
	isomaster
	android-tools-adb
	android-tools-fastboot
	android-tools-mkbootimg
	apktool
	grub-efi-amd64-signed
	fbreader
	fontforge
	xserver-xorg-input-synaptics
	net-tools
	ntpdate
	npm
	apt-file
	cpuid
	fuse2fs
	ldap-utils
	nscd
	nvidia-settings
	pm-utils
	policykit-1-gnome
	samba
	smbclient
	winbind
	arping
	iftop
	iperf
	iperf3
	iptraf-ng
	ssh
	wireshark
	testdisk
	traceroute
	libstdc++6:i386
	libgtk3-nocsd:i386
	libreoffice-base
EOF
}

remove_files=""
for package in $(list_remove_files); do
    echo $package | grep -q "^[[:space:]]*#"  || remove_files="$remove_files $package"
done 

echo "apt purge $remove_files ..."
apt purge -y $remove_files
dpkg --add-architecture i386
apt update
install_files=""
for package in $(list_install_files); do
       echo $package | grep -q "^[[:space:]]*#" || install_files="$install_files $package"
done 
echo "apt install $install_files ..."
apt install -y $install_files

