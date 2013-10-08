Reconstructor - Ubuntu Live CD Creator
	http://reconstructor.aperantis.com

REQUIREMENTS:
	If using Ubuntu 6.06 or later (may work on previous versions, but hasn't been tested...):
	- squashfs-tools (on ubuntu, add the Universe Repositories, and run  sudo apt-get install squashfs-tools)
	- make (for Qemu/VMware installation)
	- gcc (for Usplash generation and Qemu/VMware installation)
	- libbogl-dev (for Usplash generation)
	- rsync (for copying)

	If NOT using Ubuntu 6.06...
		Reconstructor uses the following:
		- python 2.4.3 (may work on other versions, but only tested on 2.4.3)
		- pygtk 2.8.6
		- squashfs-tools
		- mkisofs
		- make (for Qemu/VMware installation)
		- gcc (for Usplash generation and Qemu/VMware installation)
		- libbogl-dev (for Usplash generation)
		- rsync (for copying)

Usage: reconstructor.py [options]

Options:
  -h, --help            show this help message and exit
  -d, --debug           run as debug
  -v, --version         show version and exit
  -s, --skip-calcs      skip ISO size calculations
  -m, --manual-install  manually installs all .debs in apt cache before other
                        software
  -e, --experimental    enable experimental features
  -u, --update          automatically update to latest version



The preferred method to run Reconstructor is to open a console, change (cd) into the directory where reconstructor.py is, and type
	sudo python reconstructor.py


LANGUAGES:

To run Reconstructor in a language other than your current environment language, launch Reconstructor like the following:
	LANGUAGE=[code] sudo python reconstructor.py

For instance, to run Reconstructor in French:
	LANGUAGE=fr sudo python reconstructor.py

