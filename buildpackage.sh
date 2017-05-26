version=$(cat trunk/DEBIAN/control | grep Version: | cut -d: -f2 | sed -e "s/^ \{1,\}//g" | cut -d- -f1)
dpkg -b trunk reconstructor-$version-nx111-$(date +%Y%m%d).deb
