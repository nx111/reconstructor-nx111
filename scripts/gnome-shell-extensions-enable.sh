#!/usr/bin/sh

if gnome-extensions list | grep -q lunarcal@ailin.nemui; then
   gnome-extensions enable lunarcal@ailin.nemui
fi
if gnome-extensions list | grep -q unredirect@vaina.lt; then
   gnome-extensions enable unredirect@vaina.lt
fi

rm -f /home/$USER/.config/autostart/$(echo $(basename $0) | cut -d. -f1).desktop

