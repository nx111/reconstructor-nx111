#!/bin/sh
if [ `id -u` -ne 0 ]; then
	echo "Error: Change backgrounds need run as root! "
	exit
fi

codename=$(lsb_release -a  2>/dev/null| grep Codename | cut -f2)
relase=$(lsb_release -a  2>/dev/null| grep Release | cut -f2)
official_backgrounds="/tmp/tmp_official_backgrounds"
if [ $# -eq 0 ]; then
	picdir="/usr/share/backgrounds"
	property_xml="/usr/share/gnome-background-properties/favorite-wallpapers.xml"
	contest="/usr/share/backgrounds/contest/favorite.xml"
	filetype='-name "*.jpg"'
elif [ "$1" = "-h" -o "$1" = "--help" ]; then
	echo "Usage: $0 [picture_directory_name]"
	echo "       picture_directory_name must be in /usr/share/backgrounds"
	echo ""
	echo "e.g.  $0 westworld"
	echo "      Must have pictures in /usr/share/backgrounds/westworld"
	exit
else	
	picdir="/usr/share/backgrounds/$1"
	property_xml="/usr/share/gnome-background-properties/$1-wallpapers.xml"
	contest="/usr/share/backgrounds/contest/$1.xml"	
	filetype='-name "*.jpg" -o -name "*.png"'
fi

if [ ! -d $picdir ]; then
	echo "error: backgrounds directory \"$picdir\" not exists."
	exit
fi

#generate property xml file

echo '<?xml version="1.0" encoding="UTF-8"?>' > $property_xml
echo '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">' >> $property_xml
echo '<wallpapers>' >> $property_xml
echo ' <wallpaper deleted="false">' >> $property_xml
if [ $(basename $property_xml) = "favorite-wallpapers.xml" ]; then
	echo "   <name>Favorite Wallpapers</name>" >> $property_xml
	echo "   <filename>$contest</filename>" >> $property_xml
else
	echo "   <name>$1 Wallpapers</name>" >> $property_xml
	echo "   <filename>$contest</filename>" >> $property_xml
fi
echo '   <options>zoom</options>' >> $property_xml
echo ' </wallpaper>' >> $property_xml
rm -f $official_backgrounds
touch $official_backgrounds
find /usr/share/backgrounds/contest/ -maxdepth 1 -type f -name "*.xml" | while read f; do
	if [ $(basename $f)_ != "favorite.xml_" ]; then
		grep "<file>.*</file>" $f | sed -e "s/^[[:space:]]*<file>\(.*\)<\/file>/\1/" >> $official_backgrounds
	fi 
done

find $picdir -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.png" \) | sed -e "s/\.\///" | while read f; do
	if grep -q "$f" $official_backgrounds; then
		continue
	fi
	name=$(basename $f)
	name=$(echo ${name%.*} | sed -e "s/-background.*//" -e "s/-wallpaper.*//")
	echo ' <wallpaper>' >> $property_xml
	echo "     <name>$name</name>" >> $property_xml
	echo "     <filename>$f</filename>" >> $property_xml
	echo "     <options>zoom</options>" >> $property_xml
	echo "     <pcolor>#000000</pcolor>" >> $property_xml
	echo "     <scolor>#000000</scolor>" >> $property_xml
	echo "     <shade_type>solid</shade_type>" >> $property_xml
	echo " </wallpaper>" >> $property_xml
done
echo "</wallpapers>" >> $property_xml

##  generate contest file

echo "<background>" > $contest
echo "  <starttime>" >> $contest
echo "    <year>2009</year>" >> $contest
echo "    <month>08</month>" >> $contest
echo "    <day>04</day>" >> $contest
echo "    <hour>00</hour>" >> $contest
echo "    <minute>00</minute>" >> $contest
echo "    <second>00</second>" >> $contest
echo "  </starttime>" >> $contest
echo "<!-- This animation will start at midnight. -->" >> $contest
find $picdir -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.png" \) | sed -e "s/\.\///" | while read f; do
	if grep -q "$f" $official_backgrounds; then
		continue
	fi
	if [ "$oldfile" != "" ]; then
		echo "  <transition>" >> $contest
		echo "    <duration>5.0</duration>" >> $contest
		echo "    <from>$oldfile</from>" >> $contest
		echo "    <to>$f</to>" >> $contest
		echo "  </transition>" >> $contest
	fi
	oldfile=$f
	echo "  <static>" >> $contest
	echo "    <duration>1795.0</duration>" >> $contest
	echo "    <file>$f</file>" >> $contest
	echo "  </static>" >> $contest
done
echo "</background>" >> $contest
rm -f $official_backgrounds
