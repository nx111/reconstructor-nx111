#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Reconstructor -- http://reconstructor.aperantis.com
#    Copyright (c) 2006-2009  Reconstructor Team <reconstructor@aperantis.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import os
import time
import shutil
import optparse
import locale
import gettext
import re
import apt
import apt_pkg
import subprocess
import urllib
import configparser

path = sys.path[0]
cur_file_dir = path
if os.path.isdir(path):
     cur_file_dir = path
elif os.path.isfile(path):
         cur_file_dir = os.path.dirname(path)

sys.path.append(cur_file_dir + '/lib/')
# import Reconstructor modules
from Reconstructor.PackageHelper import PackageHelper

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import GLib
    from gi.repository import GObject
    #import Gtk.glade
    #import pango
except Exception as detail:
    print(detail)
    sys.exit(1)


def find_newest_kernel_version(base):
    ver = ''
    if re.search('/modules$', base) != None:
        cur_list = os.listdir(base)
        for item in cur_list:
                #print(item)
                full_path = os.path.join(base, item)
                if re.match(r'[0-9]+[0-9.-]+', item) and os.path.isdir(full_path):
                        if apt_pkg.version_compare(re.sub(r'([0-9\.]+-\d{2}).*','\g<1>',ver),re.sub(r'([0-9\.]+-\d{2}).*','\g<1>',item))<0:
                             ver=item
                else:
                        continue
    else:                  #if re.search('/boot$', base) != None:
        re_file = re.compile("initrd.img[-]")
        cur_list = os.listdir(base)
        for item in cur_list:
                #print(item)
                full_path = os.path.join(base, item)        
                if re_file.match(item) and os.path.isfile(full_path):
                        ver1=re_file.sub('',item)
                        if apt_pkg.version_compare(re.sub(r'([0-9\.]+-\d{2}).*','\g<1>',ver),re.sub(r'([0-9\.]+-\d{2}).*','\g<1>',ver1))<0:
                             ver=ver1
                else:
                        continue

    return ver

class Reconstructor:

    """Reconstructor - Creates custom ubuntu cds..."""
    def __init__(self):
        # vars
        self.gladefile = cur_file_dir + '/glade/gui.glade'
        self.iconFile = cur_file_dir + '/glade/app.png'
        self.logoFile = cur_file_dir + '/glade/reconstructor.png'
        self.terminalIconFile = cur_file_dir + '/glade/terminal.png'
        self.chrootxIconFile = cur_file_dir + '/glade/chrootx.png'
        self.updateIconFile = cur_file_dir + '/glade/update.png'

        self.appName = "Reconstructor"
        self.codeName = " \"\" "
        self.devInProgress = False
        self.updateId = "328"
        self.donateUrl = "https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=ejhazlett%40gmail%2ecom&item_name=Reconstructor%20Donation&item_number=R_DONATE_001&no_shipping=2&no_note=1&tax=0&currency_code=USD&lc=US&bn=PP%2dDonationsBF&charset=UTF%2d8"
        #self.devRevision = time.strftime("%y%m%d", time.gmtime())
        self.devRevision = "20200209"
        self.appVersion = "2.10.0"
        self.cdUbuntuVersion = ''
        self.altCdUbuntuVersion = ''
        self.cdUbuntuVersionNum = 0
        self.altCdUbuntuArch = ''
        self.altCdUbuntuDist = ''
        self.ubuntuCodename = ''
        self.dapperVersion = '6.06'
        self.edgyVersion = '6.10'
        self.feistyVersion = '7.04'
        self.gutsyVersion = '7.10'
        self.hardyVersion = '8.04'
        self.intrepidVersion = '8.10'
        self.jauntyVersion = '9.04'
        self.karmicVersion = '9.10'
        self.saucyVersion = '13.10'
        self.moduleDir = cur_file_dir + '/modules/'
        self.mountDir = '/media/cdrom'
        self.tmpDir = "tmp"
        self.altRemasterDir = "remaster_alt"
        self.altInitrdRoot = "initrd_alt"
        self.altRemasterRepo = "remaster_alt_repo"
        self.tmpPackageDir = "tmp_packages"
        # Alternate GPG Key vars
        self.altGpgKeyName = "Alternate Installation Automatic Signing Key"
        self.altGpgKeyComment = "Reconstructor Automatic Signing Key"
        #self.altGpgKeyEmail = "reconstructor@aperantis.com"
        #self.altGpgKeyPhrase = "titan"
        #self.altGpgKey = self.altGpgKeyName + " (" + self.altGpgKeyComment + ") <" + self.altGpgKeyEmail + ">"
        # type of disc (live/alt)
        self.discType = ""
        self.altBaseTypeStandard = 0
        self.altBaseTypeServer = 1
        self.altBaseTypeDesktop = 2
        self.customDir = ""
        self.createRemasterDir = False
        self.createCustomRoot = False
        self.createInitrdRoot = False
        self.createAltRemasterDir = False
        self.createAltInitrdRoot = False
        self.isoFilename = ""
        self.buildAltCdFilename = ""
        self.buildLiveCdFilename = ""
        self.cdArchIndex = 0
        self.setupComplete = False
        self.manualInstall = False
        self.watch = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.working = None
        self.workingDlg = None
        self.runningDebug = False
        self.interactiveEdit = False
        self.pageWelcome = 0
        self.pageDiscType = 1
        self.pageLiveSetup = 2
        self.pageLiveCustomize = 3
        self.pageLiveBuild = 4
        self.pageAltSetup = 5
        self.pageAltCustomize = 6
        self.pageAltBuild = 7
        self.pageFinish = 8
        self.gdmBackgroundColor = None
        self.enableExperimental = False
        self.gnomeBinPath = '/usr/bin/gnome-session'
        self.f = sys.stdout
        self.webUrl = "http://reconstructor.aperantis.com"
        self.updateInfo = "http://reconstructor.aperantis.com/update/info"
        self.updateFile = "http://reconstructor.aperantis.com/update/update.tar.gz"
        self.treeModel = None
        self.treeView = None

        self.modEngineKey = 'RMOD_ENGINE'
        self.modCategoryKey = 'RMOD_CATEGORY'
        self.modSubCategoryKey = 'RMOD_SUBCATEGORY'
        self.modNameKey = 'RMOD_NAME'
        self.modAuthorKey = 'RMOD_AUTHOR'
        self.modDescriptionKey = 'RMOD_DESCRIPTION'
        self.modVersionKey = 'RMOD_VERSION'
        self.modRunInChrootKey = 'RMOD_RUN_IN_CHROOT'
        self.modUpdateUrlKey = 'RMOD_UPDATE_URL'
        self.modules =  {}

        self.regexUbuntuVersion = '^DISTRIB_RELEASE=([0-9.]+)\n'
        self.regexModEngine = '^RMOD_ENGINE=([A-Za-z0-9.\s\w]+)\n'
        self.regexModCategory = '^RMOD_CATEGORY=([A-Za-z0-9\'\"\w]+)\s'
        self.regexModSubCategory = '^RMOD_SUBCATEGORY=([A-Za-z0-9\'\"\w]+)\s'
        self.regexModName = '^RMOD_NAME=([A-Za-z0-9.\-\&\,\*\/\(\)\'\"\s\w]+)\n'
        self.regexModAuthor = '^RMOD_AUTHOR=([A-Za-z0-9.\(\)\'\":\s\w]+)\n'
        self.regexModDescription = '^RMOD_DESCRIPTION=([A-Za-z0-9.\-\&\*\_\,\/\\(\)\'\"\s\w]+)\n'
        self.regexModVersion = '^RMOD_VERSION=([A-Za-z0-9.\s\w]+)\s'
        self.regexModRunInChroot = '^RMOD_RUN_IN_CHROOT=([A-Za-z0-9\w]+)\s'
        self.regexModUpdateUrl = '^RMOD_UPDATE_URL=([A-Za-z0-9:.\-\&\*\_\,\/\\(\)\'\"\s\w]+)\n'
        self.regexUbuntuAltCdVersion = '^[a-zA-Z0-9-.]*\s+([0-9.]+)\s+'
        self.regexUbuntuAltCdInfo = '([\w-]+)\s+(\d+.\d+)\s+\D+Release\s(\w+)\s+'
        self.regexUbuntuAltPackages = '^Package:\s+(\S*)\n'

        self.iterCategoryAdministration = None
        self.iterCategoryEducation = None
        self.iterCategorySoftware = None
        self.iterCategoryServers = None
        self.iterCategoryGraphics = None
        self.iterCategoryMultimedia = None
        self.iterCategoryPlugins = None
        self.iterCategoryProductivity = None
        self.iterCategoryNetworking = None
        self.iterCategoryVirtualization = None
        self.iterCategoryMisc = None
        self.moduleColumnCategory = 0
        self.moduleColumnExecute = 1
        self.moduleColumnRunOnBoot = 2
        self.moduleColumnName = 3
        self.moduleColumnVersion = 4
        self.moduleColumnAuthor = 5
        self.moduleColumnDescription = 6
        self.moduleColumnRunInChroot = 7
        self.moduleColumnUpdateUrl = 8
        self.moduleColumnPath = 9
        self.execModulesEnabled = False
        self.bootModulesEnabled = False
        self.TerminalInitialized = False
        # time command for timing operations
        self.timeCmd = subprocess.getoutput('which time') + ' -f \"\nBuild Time: %E  CPU: %P\n\"'

        # startup daemon list for speedup
        #self.startupDaemons = ('ppp', 'hplip', 'cupsys', 'festival', 'laptop-mode', 'nvidia-kernel', 'rsync', 'bluez-utils', 'mdadm')
        # shutdown scripts - without the 'K' for looping -- see  https://wiki.ubuntu.com/Teardown  for explanation
        self.shutdownScripts = ('11anacron', '11atd', '19cupsys', '20acpi-support', '20apmd', '20bittorrent', '20dbus', '20festival', '20hotkey-setup', '20makedev', '20nvidia-kernel', '20powernowd', '20rsync', '20ssh', '21acpid', '21hplip', '74bluez-utils', '88pcmcia', '88pcmciautils', '89klogd', '90syslogd')

        APPDOMAIN='reconstructor'
        LANGDIR='lang'
        # locale
        locale.setlocale(locale.LC_ALL, '')
        gettext.bindtextdomain(APPDOMAIN, LANGDIR)
        #Gtk.glade.bindtextdomain(APPDOMAIN, LANGDIR)
        #Gtk.glade.textdomain(APPDOMAIN)
        gettext.textdomain(APPDOMAIN)
        gettext.install(APPDOMAIN, LANGDIR)

        # setup glade widget tree
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.gladefile)


        # check for user
        if os.getuid() != 0 :
            self.builder.get_object("windowMain").hide()

        # create signal dictionary and connect
        dic = { "on_buttonNext_clicked" : self.on_buttonNext_clicked,
            "on_buttonBack_clicked" : self.on_buttonBack_clicked,
            "on_buttonBrowseWorkingDir_clicked" : self.on_buttonBrowseWorkingDir_clicked,
            "on_buttonBrowseIsoFilename_clicked" : self.on_buttonBrowseIsoFilename_clicked,
            "on_checkbuttonBuildIso_toggled" : self.on_checkbuttonBuildIso_toggled,
            "on_buttonBrowseLiveCdFilename_clicked" : self.on_buttonBrowseLiveCdFilename_clicked,
            "on_buttonBrowseGnomeDesktopWallpaper_clicked" : self.on_buttonBrowseGnomeDesktopWallpaper_clicked,
            "on_buttonBrowseGnomeFont_clicked" : self.on_buttonBrowseGnomeFont_clicked,
            "on_buttonBrowseGnomeDocumentFont_clicked" : self.on_buttonBrowseGnomeDocumentFont_clicked,
            "on_buttonBrowseGnomeDesktopFont_clicked": self.on_buttonBrowseGnomeDesktopFont_clicked,
            "on_buttonBrowseGnomeDesktopTitleBarFont_clicked" : self.on_buttonBrowseGnomeDesktopTitleBarFont_clicked,
            "on_buttonBrowseGnomeFixedFont_clicked" : self.on_buttonBrowseGnomeFixedFont_clicked,
            "on_buttonImportGnomeTheme_clicked" : self.on_buttonImportGnomeTheme_clicked,
            "on_buttonImportGnomeThemeIcons_clicked" : self.on_buttonImportGnomeThemeIcons_clicked,
            "on_buttonImportGdmTheme_clicked" : self.on_buttonImportGdmTheme_clicked,
            "on_buttonSoftwareCalculateIsoSize_clicked" : self.on_buttonSoftwareCalculateIsoSize_clicked,
            "on_buttonSoftwareApply_clicked" : self.on_buttonSoftwareApply_clicked,
            "on_buttonInteractiveEditLaunch_clicked" : self.on_buttonInteractiveEditLaunch_clicked,
            "on_buttonInteractiveClear_clicked" : self.on_buttonInteractiveClear_clicked,
            "on_buttonOptimizeShutdownRestore_clicked" : self.on_buttonOptimizeShutdownRestore_clicked,
            "on_checkbuttonOptimizationStartupEnable_toggled" : self.on_checkbuttonOptimizationStartupEnable_toggled,
            "on_buttonCustomizeLaunchTerminal_clicked" : self.on_buttonCustomizeLaunchTerminal_clicked,
            "on_buttonCustomizeLaunchChrootX_clicked" : self.on_buttonCustomizeLaunchChrootX_clicked,
            "on_buttonBurnIso_clicked" : self.on_buttonBurnIso_clicked,
            "on_buttonCheckUpdates_clicked" : self.on_buttonCheckUpdates_clicked,
            "on_buttonModulesAddModule_clicked" : self.on_buttonModulesAddModule_clicked,
            "on_buttonModulesClearRunOnBoot_clicked" : self.on_buttonModulesClearRunOnBoot_clicked,
            "on_buttonModulesUpdateModule_clicked" : self.on_buttonModulesUpdateModule_clicked,
            "on_buttonBrowseAltWorkingDir_clicked" : self.on_buttonBrowseAltWorkingDir_clicked,
            "on_buttonBrowseAltIsoFilename_clicked" : self.on_buttonBrowseAltIsoFilename_clicked,
            "on_buttonAltIsoCalculate_clicked" : self.on_buttonAltIsoCalculate_clicked,
            "on_checkbuttonAltCreateRemasterDir_clicked" : self.on_checkbuttonAltCreateRemasterDir_clicked,
            "on_buttonAptRepoImportGpgKey_clicked" : self.on_buttonAptRepoImportGpgKey_clicked,
            "on_buttonAltPackagesImportGpgKey_clicked" : self.on_buttonAltPackagesImportGpgKey_clicked,
            "on_buttonAltPackagesApply_clicked" : self.on_buttonAltPackagesApply_clicked,
            "on_checkbuttonAltBuildIso_toggled" : self.on_checkbuttonAltBuildIso_toggled,
            "on_buttonBrowseAltCdFilename_clicked" : self.on_buttonBrowseAltCdFilename_clicked,
            "on_buttonDonate_clicked" : self.on_buttonDonate_clicked,
            "on_windowMain_delete_event" : self.exitApp, #Gtk.main_quit,
            "on_windowMain_destroy" : self.exitApp }
        self.builder.connect_signals(dic)

        # add command option parser
        parser = optparse.OptionParser()
        parser.add_option("-d", "--debug",
                    action="store_true", dest="debug", default=False,
                    help="run as debug")
        parser.add_option("-v", "--version",
                    action="store_true", dest="version", default=False,
                    help="show version and exit")
        parser.add_option("-m", "--manual-install",
                    action="store_true", dest="manualinstall", default=False,
                    help="manually installs all .debs in apt cache before other software")
        parser.add_option("-e", "--experimental",
                    action="store_true", dest="experimental", default=False,
                    help="enable experimental features")
        parser.add_option("-u", "--update",
                    action="store_true", dest="update", default=False,
                    help="automatically update to latest version")
        parser.add_option("-w", "--workdir",
                   action="store", dest="workdir", default="", metavar="[/path/to/directory]",
                   help="Specify default working directory.")
        (options, args) = parser.parse_args()

        if options.debug == True:
            self.runningDebug = True
            self.builder.get_object("notebookWizard").set_show_tabs(True)
            print(_('INFO: Running Debug...'))
        else:
            # hide tabs
            #if self.builder.get_object("notebookWizard") != None:
            self.builder.get_object("notebookWizard").set_show_tabs(False)
        if options.version == True:
            print(" ")
            print(self.appName + " -- (c) Reconstructor Team, 2006-2009")
            print("       Version: " + self.appVersion + " rev. " + self.updateId)
            print("        http://reconstructor.aperantis.com")
            print(" ")
            #Gtk.main_quit()
            sys.exit(0)
        if options.manualinstall == True:
            print(_('INFO: Manually Installing .deb archives in cache...'))
            self.manualInstall = True
        if options.experimental == True:
            print(_('INFO: Enabling Experimental Features...'))
            self.enableExperimental = True
        if options.update == True:
            print(_('INFO: Updating...'))
            self.update()

        # print copyright
        print(" ")
        print(self.appName + " -- (c) Reconstructor Team, 2006-2009")
        print("\t\tVersion: " + self.appVersion)
        print("\thttp://reconstructor.aperantis.com")
        print(" ")

        # set icons & logo
        self.builder.get_object("windowMain").set_icon_from_file(self.iconFile)
        self.builder.get_object("imageLogo").set_from_file(self.logoFile)
        imgTerminal = Gtk.Image()
        imgTerminal.set_from_file(self.terminalIconFile)
        self.builder.get_object("buttonCustomizeLaunchTerminal").set_image(imgTerminal)
        imgChrootX = Gtk.Image()
        imgChrootX.set_from_file(self.chrootxIconFile)
        self.builder.get_object("buttonCustomizeLaunchChrootX").set_image(imgChrootX)
        imgUpdate = Gtk.Image()
        imgUpdate.set_from_file(self.updateIconFile)
        self.builder.get_object("buttonCheckUpdates").set_image(imgUpdate)

        # check for existing mount dir
        if os.path.exists(self.mountDir) == False:
            print(_('INFO: Creating mount directory...'))
            os.makedirs(self.mountDir)

        # set app title
        if self.devInProgress:
            self.builder.get_object("windowMain").set_title(self.appName + self.codeName + "  Build " + self.devRevision)
        else:
            self.builder.get_object("windowMain").set_title(self.appName)

        # check dependencies
        self.checkDependencies()

        # set version
        self.builder.get_object("labelVersion").set_text('version ' + self.appVersion)

        # hide back button initially
        self.builder.get_object("buttonBack").hide()
        # set default live cd text color
        #self.builder.get_object("colorbuttonBrowseLiveCdTextColor").set_color(Gdk.color_parse("#FFFFFF"))
        # set default working directory path
        if options.workdir != "":
            self.builder.get_object("entryWorkingDir").set_text(options.workdir)
            self.builder.get_object("entryAltWorkingDir").set_text(options.workdir)
        else:
            self.builder.get_object("entryWorkingDir").set_text(os.path.join(os.environ['HOME'], "reconstructor"))
            self.builder.get_object("entryAltWorkingDir").set_text(os.path.join(os.environ['HOME'], "reconstructor"))
	
        self.builder.get_object("entryLiveIsoFilename").set_text(os.path.join(os.environ['HOME'], "ubuntu-custom-live.iso"))
        self.builder.get_object("entryAltBuildIsoFilename").set_text(os.path.join(os.environ['HOME'], "ubuntu-custom-alt.iso"))
        # set default descriptions
        cdDesc = _('Ubuntu Custom')
        self.builder.get_object("entryLiveCdDescription").set_text(cdDesc)
        self.builder.get_object("entryBuildAltCdDescription").set_text(cdDesc)
        # set default cd architectures
        self.builder.get_object("comboboxLiveCdArch").set_active(0)
        self.builder.get_object("comboboxAltBuildArch").set_active(0)

        # set default customDir form config file
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(os.path.join(os.environ['HOME'], ".reconstructor"))
        try:
             self.customDir = config.get('global','workdir')
        except:
             self.customDir = ''

    def run_generator(self, function):
        gen = function()
        GLib.idle_add(lambda: next(gen, False))

    def isMounted(self,path):
        error = subprocess.getoutput("grep -c \"[[:space:]]" + path +"\" /proc/mounts")
        # print('..check mounted: ' + "grep -c \"" + path +"\" /proc/mounts  (" + error +")")
        if error != '0':
            return True
        else:
            return False

    def showProgress(self,text=False,fraction=False):
        if text:
            self.builder.get_object("labelStatus").set_text(text)
        if fraction:
            self.builder.get_object("progressbar").set_fraction(fraction)
        #print("DEBUG: showProgress  result: text=" + self.builder.get_object("labelStatus").get_text() + " [[fraction="+str(self.builder.get_object("progressbar").get_fraction()) + "]]")


    def checkChroot(self):
        # check vmlinuz and initrd
        print('Check Chroot ...')
        kernelFileReady = False
        kernelVersion = ''
        kernelFile = ''
        casper_initram_file=subprocess.getoutput("grep \"initrd=/casper/\" -Ir " + os.path.join(self.customDir,'remaster','isolinux') + " | head -n 1 | sed -e \"s/.*initrd=\/casper\/\(\w\+\).*/\\1/g\"")
        casper_kernel_file=subprocess.getoutput("grep \"initrd=/casper/\" -Ir " + os.path.join(self.customDir,'remaster','isolinux') + " | head -n 1 | sed -e \"s/.*kernel\W\+\/casper\/\(\w\+\).*/\\1/g\"")

        if os.path.lexists(os.path.join(self.customDir,"root/boot/vmlinuz")):
            kernelFile = subprocess.getoutput("readlink " + os.path.join(self.customDir,"root/boot/vmlinuz"))
        elif os.path.lexists(os.path.join(self.customDir,"root/vmlinuz")):
            kernelFile = subprocess.getoutput("readlink " + os.path.join(self.customDir,"root/boot/vmlinuz"))

        if kernelFile != '':
            kernelVersion = subprocess.getoutput("basename " + kernelFile +" | sed -e 's/vmlinuz-//'")
        if kernelVersion == '':
            kernelVersion = find_newest_kernel_version(os.path.join(self.customDir, "root/lib/modules"))
        #print('kernelVersion:'+kernelVersion + " kernelFile:" + kernelFile)
        if kernelVersion != '':
            if os.path.exists(os.path.join(self.customDir,"root/boot/vmlinuz-"+kernelVersion)) == False:
                if os.path.exists(os.path.join(self.customDir,"remaster/casper", casper_kernel_file)):
                     subprocess.getoutput('cp '+ os.path.join(self.customDir,"remaster/casper", casper_kernel_file) + ' ' +  os.path.join(self.customDir,"root/boot/vmlinuz-"+kernelVersion))
            if os.path.exists(os.path.join(self.customDir,"root/boot/initrd.img-"+kernelVersion)) == False:
                if os.path.exists(os.path.join(self.customDir,"remaster/casper", casper_initram_file)):
                    subprocess.getoutput('cp '+ os.path.join(self.customDir,"remaster/casper", casper_initram_file) + ' ' +  os.path.join(self.customDir,"root/boot/initrd.img-"+kernelVersion))
            if kernelFile:
                if (os.path.exists(os.path.join(self.customDir,"root/boot/"+kernelFile))):
                    kernelFileReady = True
            if kernelFileReady == True:
                #print('Recreate Kernel File Link....')
                if os.path.exists(os.path.join(self.customDir,"root/boot/vmlinuz")):
                    os.remove(os.path.join(self.customDir, "root/boot/vmlinuz"))
                    os.symlink('vmlinuz-' + kernelVersion, os.path.join(self.customDir, "root/boot/vmlinuz"))
                if os.path.exists(os.path.join(self.customDir,"root/vmlinuz")):
                    os.remove(os.path.join(self.customDir, "root/vmlinuz"))
                    os.symlink('boot/vmlinuz-' + kernelVersion, os.path.join(self.customDir, "root/vmlinuz"))

                if os.path.exists(os.path.join(self.customDir,"root/boot/initrd.img")):
                    os.remove(os.path.join(self.customDir, "root/boot/initrd.img"))
                    os.symlink('initrd.img-' + kernelVersion, os.path.join(self.customDir, "root/boot/initrd.img"))
                if os.path.exists(os.path.join(self.customDir,"root/initrd.img")):
                    os.remove(os.path.join(self.customDir, "root/initrd.img"))
                    os.symlink('boot/initrd.img-' + kernelVersion, os.path.join(self.customDir, "root/initrd.img"))

        # check polkit rules for running pkexec gedit/nautilus
        if apt_pkg.version_compare(self.cdUbuntuVersion, '18.04') >= 0:
            mydir=os.path.split(os.path.realpath(__file__))[0]
            if subprocess.getoutput('grep gedit -r ' + os.path.join(self.customDir,"root/usr/share/polkit-1/actions") + ' | wc -l') == '0':
               subprocess.getoutput('cp -f' + os.path.join(mydir, 'polkit-1/actions/org.gnome.gedit.policy') + ' ' \
                    +  os.path.join(self.customDir,"root/usr/share/polkit-1/actions"))
            if subprocess.getoutput('grep nautilus -r ' + os.path.join(self.customDir,"root/usr/share/polkit-1/actions") + ' | wc -l') == '0':
                subprocess.getoutput('cp -f' + os.path.join(mydir, 'polkit-1/actions/org.gnome.nautilus.policy') + ' ' \
                +  os.path.join(self.customDir,"root/usr/share/polkit-1/actions"))

    # Check for Application Dependencies
    def checkDependencies(self):
        print(_('Checking dependencies...'))
        dependList = ''
        if subprocess.getoutput('which mksquashfs') == '':
            print(_('squashfs-tools NOT FOUND (needed for Root FS extraction)'))
            dependList += 'squashfs-tools\n'
        if subprocess.getoutput('which chroot') == '':
            print(_('chroot NOT FOUND (needed for Root FS customization)'))
            dependList += 'chroot\n'
        if subprocess.getoutput('which mkisofs') == '':
            print(_('mkisofs NOT FOUND (needed for ISO generation)'))
            dependList += 'mkisofs\n'
        if subprocess.getoutput('which gcc') == '':
            print(_('gcc NOT FOUND (needed for VMWare/Qemu installation)'))
            dependList += 'gcc\n'
        if subprocess.getoutput('which make') == '':
            print(_('make NOT FOUND (needed for VMWare/Qemu installation)'))
            dependList += 'make\n'
        if subprocess.getoutput('which rsync') == '':
            print(_('rsync NOT FOUND (needed for Remastering ISO)'))
            dependList += 'rsync\n'
        if subprocess.getoutput('which Xephyr') == '':
            print(_('Xephyr NOT Found (needed for ChrootX)'))
            dependList += 'xserver-xephyr\n'
         # gpg
        if subprocess.getoutput('which gpg') == '':
            print(_('gpg NOT FOUND (needed for Alternate Key Signing)'))
            dependList += 'gpg\n'
        # dpkg-buildpackage
        if subprocess.getoutput('which dpkg-buildpackage') == '':
            print(_('dpkg-dev NOT FOUND (needed for Alternate Key Package Building)'))
            dependList += 'dpkg-dev\n'
        # xterm
        if subprocess.getoutput('which xterm') == '':
            print(_('xterm NOT FOUND (needed for gnome-terminal fallback)'))
            dependList += 'xterm\n'
        # fakeroot
        if subprocess.getoutput('which fakeroot') == '':
            print(_('fakeroot NOT FOUND (needed for Alternate Key Package Building)'))
            dependList += 'fakeroot\n'
        # apt-ftparchive
        if subprocess.getoutput('which apt-ftparchive') == '':
            print(_('apt-utils NOT FOUND (needed for Extra Repository Generation)'))
            dependList += 'apt-utils\n'
        if dependList != '':
            print(_('\nThe following dependencies are not met: '))
            print(dependList)
            print(_('Please install the dependencies and restart reconstructor.'))
            # show warning dialog
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label(" ")
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblText = _('  <b>Reconstructor may not work correctly.</b>\nThe following dependencies are not met: ')
            lbl = Gtk.Label(lblText)
            lbl.set_use_markup(True)
            lblInfo = Gtk.Label(dependList)
            lblFixText = _('Install the dependencies and restart reconstructor?')
            lblFix = Gtk.Label(lblFixText)
            warnDlg.vbox.pack_start(lbl, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(lblFix, expand=True, fill=True, padding=0)
            lbl.show()
            lblInfo.show()
            lblFix.show()
            #warnDlg.show()
            response = warnDlg.run()
            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
                # use apt to install
                #print('apt-get install -y ' + dependList.replace('\n', ' '))
                installTxt = _('Installing dependencies: ')
                print(installTxt + dependList.replace('\n', ' '))
                subprocess.getoutput('apt-get install -y ' + dependList.replace('\n', ' '))
                sys.exit(0)
            else:
                warnDlg.destroy()

        else:
            print(_('Ok.'))


    # load live cd ubuntu version
    def loadCdVersion(self):
        if self.customDir != '':
            # reset version
            self.cdUbuntuVersion = 'unknown'
            # build regex
            r = re.compile(self.regexUbuntuVersion, re.IGNORECASE)
            f = open(os.path.join(self.customDir, "root/etc/lsb-release"), 'r')
            for l in f:
                if r.match(l) != None:
                    self.cdUbuntuVersion = r.match(l).group(1)
            f.close()

            print('Ubuntu Version: ' + self.cdUbuntuVersion)
            self.cdUbuntuVersionNum = float(re.sub(r'^(\d+\.\d+)\D*.*','\g<1>',self.cdUbuntuVersion))
            # BUGFIX - fixes string from getting longer and longer and longer...
            self.builder.get_object("labelCustomizeUbuntuLiveVersion").set_text("Ubuntu Live CD Version: " + self.cdUbuntuVersion)
        return

    # Check for Updates (GUI)
    def checkForUpdates(self):
        urllib.urlretrieve(self.updateInfo, ".r-info")
        if os.path.exists('.r-info'):
            f = open('.r-info', 'r')
            updateVersion = f.readline()
            updateInfo = f.read()
            f.close()
            fApp = int(self.updateId)
            fUpdate = int(updateVersion)
            if fUpdate > fApp:
                updateDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                updateDlg.add_buttons(Gtk.STOCK_NO, Gtk.RESPONSE_NO, Gtk.STOCK_YES, Gtk.ResponseType.OK)
                updateDlg.set_icon_from_file(self.iconFile)
                updateDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                updateDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblNewVersion = Gtk.Label('New version available...')
                updateDlg.vbox.pack_start(lblNewVersion, expand=True, fill=True, padding=0)
                lblNewVersion.show()
                lblInfo = Gtk.Label(updateInfo)
                lblInfo.set_use_markup(True)
                updateDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
                lblInfo.show()
                lblConfirm = Gtk.Label('Update?')
                updateDlg.vbox.pack_start(lblConfirm, expand=True, fill=True, padding=0)
                lblConfirm.show()

                response = updateDlg.run()
                if response == Gtk.ResponseType.OK:
                    updateDlg.destroy()
                    self.setBusyCursor()
                    self.update(silent=True)
                    self.exitApp()
                else:
                    print(_('Update cancelled...'))
                    updateDlg.destroy()
            else:
                updateDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                updateDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
                updateDlg.set_icon_from_file(self.iconFile)
                updateDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                updateDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblNewVersion = Gtk.Label('Reconstructor is at the latest version.')
                updateDlg.vbox.pack_start(lblNewVersion, expand=True, fill=True, padding=0)
                lblNewVersion.show()

                response = updateDlg.run()
                if response == Gtk.ResponseType.OK:
                    updateDlg.destroy()
                else:
                    updateDlg.destroy()

        self.setDefaultCursor()
        # cleanup
        if os.path.exists('.r-info'):
            subprocess.getoutput('rm -f .r-info')
        if os.path.exists('.update.tar.gz'):
            subprocess.getoutput('rm -f .update.tar.gz')

    # Gives the user the choice to reboot their computer
    def suggestReboot(self, reason):
        rebootDlg = Gtk.Dialog(title='Warning!', parent=None, flags=0)
        rebootDlg.add_buttons=(Gtk.STOCK_NO, Gtk.RESPONSE_NO, Gtk.STOCK_YES, Gtk.ResponseType.OK)
        rebootDlg.set_icon_from_file(self.iconFile)
        rebootDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        rebootDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lblReason = Gtk.Label(reason)
        rebootDlg.vbox.pack_start(lblReason, expand=True, fill=True, padding=0)
        lblReason.show()
        lblConfirm = Gtk.Label('<b>Reboot Now?</b>')
        lblConfirm.set_use_markup(True)
        rebootDlg.vbox.pack_start(lblConfirm, expand=True, fill=True, padding=0)
        lblConfirm.show()

        print(_('Warning! ' + reason + ' Reboot Now?'))

        response = rebootDlg.run()
        if response == Gtk.ResponseType.OK:
            rebootDlg.destroy()
            subprocess.getoutput('reboot')
        else:
            print(_('User chose NOT to reboot...'))
            rebootDlg.destroy()

    def showDownloadProgress(self, transferCount, blockSize, totalSize):
        #f.write('------------ Download Progress ------------')
        self.f.flush()
        if (transferCount * blockSize) < totalSize:
            self.f.write(str((transferCount * blockSize) / 1000) + 'KB of ' + str(totalSize / 1000) + 'KB\n')
        else:
            # HACK: report the same size to avoid confusion by rounding
            self.f.write(str(totalSize / 1000) + 'KB of ' + str(totalSize / 1000) + 'KB\n')
        #f.write('-------------------------------------------')


    # Updates reconstructor
    def update(self,silent=False):
        try:
            # update
            #print(_('Getting update info...'))
            urllib.urlretrieve(self.updateInfo, ".r-info")
            if os.path.exists('.r-info'):
                f = open('.r-info', 'r')
                updateVersion = f.readline()
                updateInfo = f.read()
                f.close()
                fApp = int(self.updateId)
                fUpdate = int(updateVersion)
                #print(('Current: ' + str(fApp) + ' -- Available: ' + str(fUpdate)))
                if fUpdate > fApp:
                    if silent == False:
                        print(_('New version available...'))
                        print(updateInfo)
                        updateText = _('Download and Install Update (y/n):')
                        doUpdate = raw_input(updateText)
                        if doUpdate.lower() == 'y':
                            print(_('Getting update...'))
                            urllib.urlretrieve(self.updateFile, ".update.tar.gz", self.showDownloadProgress)
                            print(_('\nInstalling update...'))
                            subprocess.getoutput('tar zxf .update.tar.gz')
                            print(_('Updated.  Please restart reconstructor.\n'))
                        else:
                            print(_('Update cancelled.'))
                    else:
                        # silent passed
                        print(_('Getting update...'))
                        urllib.urlretrieve(self.updateFile, ".update.tar.gz", self.showDownloadProgress)
                        print(_('\nInstalling update...'))
                        subprocess.getoutput('tar zxf .update.tar.gz')
                        print(_('Updated.  Please restart reconstructor.\n'))
                else:
                    print(_('Reconstructor is at the latest version.\n'))
                # cleanup
                if os.path.exists('.r-info'):
                    subprocess.getoutput('rm -f .r-info')
                if os.path.exists('.update.tar.gz'):
                    subprocess.getoutput('rm -f .update.tar.gz')
            sys.exit(0)
        except Exception as detail:
            # HACK: nasty hack - update always throws exception, so ignore...
            #print(detail)
            sys.exit(0)

    # Handle Module Properties
    def getModuleProperties(self, moduleName):
        #print(_('Loading module properties...'))

        fMod = open(os.path.join(self.moduleDir, moduleName), 'r')

        properties = {}

        # search for mod properties
        modCategory = ''
        modSubCategory = ''
        modName = ''
        modVersion = ''
        modAuthor = ''
        modDescription = ''
        modRunInChroot = None
        modUpdateUrl = ''

      # HACK: regex through module to get info
        reModCategory = re.compile(self.regexModCategory, re.IGNORECASE)
        reModSubCategory = re.compile(self.regexModSubCategory, re.IGNORECASE)
        reModName = re.compile(self.regexModName, re.IGNORECASE)
        reModVersion = re.compile(self.regexModVersion, re.IGNORECASE)
        reModAuthor = re.compile(self.regexModAuthor, re.IGNORECASE)
        reModDescription = re.compile(self.regexModDescription, re.IGNORECASE)
        reModRunInChroot = re.compile(self.regexModRunInChroot, re.IGNORECASE)
        reModUpdateUrl = re.compile(self.regexModUpdateUrl, re.IGNORECASE)

        for line in fMod:
            if reModCategory.match(line) != None:
                modCategory = reModCategory.match(line).group(1)
            if reModSubCategory.match(line) != None:
                modSubCategory = reModSubCategory.match(line).group(1)
            if reModName.match(line) != None:
                modName = reModName.match(line).group(1)
            if reModVersion.match(line) != None:
                modVersion = reModVersion.match(line).group(1)
            if reModAuthor.match(line) != None:
                modAuthor = reModAuthor.match(line).group(1)
            if reModDescription.match(line) != None:
                modDescription = reModDescription.match(line).group(1)
            if reModRunInChroot.match(line) != None:
                modRunInChroot = reModRunInChroot.match(line).group(1)
            if reModUpdateUrl.match(line) != None:
                modUpdateUrl = reModUpdateUrl.match(line).group(1)
        fMod.close()

        # remove single and double quotes if any
        modCategory = modCategory.replace("'", "")
        modCategory = modCategory.replace('"', '')
        modSubCategory = modSubCategory.replace("'", "")
        modSubCategory = modSubCategory.replace('"', '')
        modName = modName.replace("'", "")
        modName = modName.replace('"', '')
        modAuthor = modAuthor.replace("'", "")
        modAuthor = modAuthor.replace('"', '')
        modDescription = modDescription.replace("'", "")
        modDescription = modDescription.replace('"', '')
        modUpdateUrl = modUpdateUrl.replace("'", "")
        modUpdateUrl = modUpdateUrl.replace('"', '')

        properties[self.modEngineKey] = 'None'
        properties[self.modCategoryKey] = modCategory
        properties[self.modSubCategoryKey] = modSubCategory
        properties[self.modNameKey] = modName
        properties[self.modAuthorKey] = modAuthor
        properties[self.modDescriptionKey] = modDescription
        properties[self.modRunInChrootKey] = modUpdateUrl
        properties[self.modVersionKey] = modVersion
        properties[self.modUpdateUrlKey] = modUpdateUrl

        return properties

    # Loads modules
    def loadModules(self):
        #print(_('Loading modules...'))
        # generate model for treeview
        # create treestore of (install(bool), modulename, version, author, description, runInChroot(hidden), filepath(hidden))
        self.treeModel = None
        self.treeModel = Gtk.TreeStore(GObject.TYPE_STRING, GObject.TYPE_BOOLEAN, GObject.TYPE_BOOLEAN, GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_BOOLEAN, GObject.TYPE_STRING, GObject.TYPE_STRING)
        # load categories self.treeModel
        # root categories
        self.iterCategorySoftware = self.treeModel.insert_before(None, None)
        self.treeModel.set_value(self.iterCategorySoftware, 0, 'Software')
        # administration
        self.iterCategoryAdministration = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryAdministration, 0, 'Administration')
        # education
        self.iterCategoryEducation = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryEducation, 0, 'Education')
        # servers
        self.iterCategoryServers = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryServers, 0, 'Servers')
        # graphics
        self.iterCategoryGraphics = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryGraphics, 0, 'Graphics')
        # multimedia
        self.iterCategoryMultimedia = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryMultimedia, 0, 'Multimedia')
        # networking
        self.iterCategoryNetworking = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryNetworking, 0, 'Networking')
        # plugins
        self.iterCategoryPlugins = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryPlugins, 0, 'Plugins')
        # productivity
        self.iterCategoryProductivity = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryProductivity, 0, 'Productivity')
        # virtualization
        self.iterCategoryVirtualization = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryVirtualization, 0, 'Virtualization')
        # miscellaneous
        self.iterCategoryMisc = self.treeModel.insert_before(self.iterCategorySoftware, None)
        self.treeModel.set_value(self.iterCategoryMisc, 0, 'Miscellaneous')

        # load modules into the treestore
        for root, dirs, files in os.walk(self.moduleDir):
                for f in files:
                    r, ext = os.path.splitext(f)
                    if ext == '.rmod':
                        #print('Module: ' + f.replace('.rmod', '') + ' found...')

                        modPath = os.path.join(self.moduleDir, f)

                        # Refactoring! triplem
                        modProps = self.getModuleProperties(f)
                        modSubCategory = modProps[self.modSubCategoryKey]

                        #if self.modules.has_key(modProps[self.modNameKey]):
                        #    print("The module is already present")

                        self.modules[modProps[self.modNameKey]] = modProps

                        # load into self.treeModel
                        #iter = self.treeModel.insert_before(iterCatOther, None)
                        if modSubCategory == 'Administration':
                            iter = self.treeModel.insert_before(self.iterCategoryAdministration, None)
                        elif modSubCategory == 'Education':
                            iter = self.treeModel.insert_before(self.iterCategoryEducation, None)
                        elif modSubCategory == 'Servers':
                            iter = self.treeModel.insert_before(self.iterCategoryServers, None)
                        elif modSubCategory == 'Graphics':
                            iter = self.treeModel.insert_before(self.iterCategoryGraphics, None)
                        elif modSubCategory == 'Multimedia':
                            iter = self.treeModel.insert_before(self.iterCategoryMultimedia, None)
                        elif modSubCategory == 'Networking':
                            iter = self.treeModel.insert_before(self.iterCategoryNetworking, None)
                        elif modSubCategory == 'Plugins':
                            iter = self.treeModel.insert_before(self.iterCategoryPlugins, None)
                        elif modSubCategory == 'Productivity':
                            iter = self.treeModel.insert_before(self.iterCategoryProductivity, None)
                        elif modSubCategory == 'Virtualization':
                            iter = self.treeModel.insert_before(self.iterCategoryVirtualization, None)
                        else:
                            iter = self.treeModel.insert_before(self.iterCategoryMisc, None)

                        self.treeModel.set_value(iter, self.moduleColumnExecute, False)
                        self.treeModel.set_value(iter, self.moduleColumnRunOnBoot, False)
                        self.treeModel.set_value(iter, self.moduleColumnName, modProps[self.modNameKey])
                        self.treeModel.set_value(iter, self.moduleColumnVersion, modProps[self.modVersionKey])
                        self.treeModel.set_value(iter, self.moduleColumnAuthor, modProps[self.modAuthorKey])
                        self.treeModel.set_value(iter, self.moduleColumnDescription, modProps[self.modDescriptionKey])
                        self.treeModel.set_value(iter, self.moduleColumnRunInChroot, bool(modProps[self.modRunInChrootKey]))
                        self.treeModel.set_value(iter, self.moduleColumnUpdateUrl, modProps[self.modUpdateUrlKey])
                        self.treeModel.set_value(iter, self.moduleColumnPath, modPath)
                        #print(modName, modVersion, modAuthor, modDescription, modUseXterm, modRunInChroot, modPath)
                        # set default sort by category
                        self.treeModel.set_sort_column_id(self.moduleColumnCategory, Gtk.SortType.ASCENDING)
                        # build treeview
                        #view = self.treeView
                        view = Gtk.TreeView.new_with_model(self.treeModel)
                        view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
                        view.set_property('search-column', self.moduleColumnName)
                        view.set_reorderable(False)
                        view.set_enable_search(True)
                        view.set_headers_clickable(True)
                        #view.set_rules_hint(True)
                        view.connect("row-activated", self.on_treeitem_row_activated)
                        self.builder.get_object("buttonModulesViewModule").connect("clicked", self.on_buttonModulesViewModule_clicked, view)
                        self.builder.get_object("buttonModulesUpdateModule").connect("clicked", self.on_buttonModulesUpdateModule_clicked, view)
                        #view.set_model(model)
                        # category column
                        rendererCategory = Gtk.CellRendererText()
                        categoryText = _('Category')
                        columnCategory = Gtk.TreeViewColumn(categoryText, rendererCategory, text=self.moduleColumnCategory)
                        columnCategory.set_sort_column_id(self.moduleColumnCategory)
                        view.append_column(columnCategory)
                        # execute column
                        rendererExecute = Gtk.CellRendererToggle()
                        rendererExecute.set_property('activatable', True)
                        rendererExecute.connect("toggled", self.on_treeitemExecute_toggled, self.treeModel)
                        executeText = _('Execute')
                        columnExecute = Gtk.TreeViewColumn(executeText, rendererExecute, active=self.moduleColumnExecute)
                        view.append_column(columnExecute)
                        # run on boot
                        rendererRunOnBoot = Gtk.CellRendererToggle()
                        rendererRunOnBoot.set_property('activatable', True)
                        rendererRunOnBoot.connect("toggled", self.on_treeitemRunOnBoot_toggled, self.treeModel)
                        runOnBootText = _('Run on boot')
                        columnRunOnBoot = Gtk.TreeViewColumn(runOnBootText, rendererRunOnBoot, active=self.moduleColumnRunOnBoot)
                        view.append_column(columnRunOnBoot)
                        # module name column
                        rendererModName = Gtk.CellRendererText()
                        modNameText = _('Module')
                        columnModName = Gtk.TreeViewColumn(modNameText, rendererModName, text=self.moduleColumnName)
                        columnModName.set_resizable(True)
                        columnModName.set_sort_column_id(self.moduleColumnName)
                        view.append_column(columnModName)
                        # module version column
                        rendererModVersion = Gtk.CellRendererText()
                        rendererModVersion.set_property('xalign', 0.5)
                        modVersionText = _(' Module Version')
                        columnModVersion = Gtk.TreeViewColumn(modVersionText, rendererModVersion, text=self.moduleColumnVersion)
                        view.append_column(columnModVersion)
                        # module author column
                        rendererModAuthor = Gtk.CellRendererText()
                        modAuthorText = _('Author')
                        columnModAuthor = Gtk.TreeViewColumn(modAuthorText, rendererModAuthor, text=self.moduleColumnAuthor)
                        columnModAuthor.set_resizable(True)
                        columnModAuthor.set_sort_column_id(self.moduleColumnAuthor)
                        view.append_column(columnModAuthor)
                        # module description column
                        rendererModDescription = Gtk.CellRendererText()
                        modDescriptionText = _('Description')
                        columnModDescription = Gtk.TreeViewColumn(modDescriptionText, rendererModDescription, text=self.moduleColumnDescription)
                        columnModDescription.set_resizable(True)
                        view.append_column(columnModDescription)
                        # module run in chroot column
                        rendererModRunInChroot = Gtk.CellRendererToggle()
                        modRunInChrootText = _('Run in Chroot')
                        columnModRunInChroot = Gtk.TreeViewColumn(modRunInChrootText, rendererModRunInChroot, active=self.moduleColumnRunInChroot)
                        # show column if running debug
                        if self.runningDebug == True:
                            columnModRunInChroot.set_property('visible', True)
                        else:
                            columnModRunInChroot.set_property('visible', False)
                        view.append_column(columnModRunInChroot)
                        # module update url column
                        rendererModUpdateUrl = Gtk.CellRendererText()
                        modUpdateUrlText = _('Update URL')
                        columnModUpdateUrl = Gtk.TreeViewColumn(modUpdateUrlText, rendererModUpdateUrl, text=self.moduleColumnUpdateUrl)
                        # show column if running debug
                        if self.runningDebug == True:
                            columnModUpdateUrl.set_property('visible', True)
                        else:
                            columnModUpdateUrl.set_property('visible', False)
                        view.append_column(columnModUpdateUrl)
                        # module path column
                        rendererModPath = Gtk.CellRendererText()
                        modPathText = _('Path')
                        columnModPath = Gtk.TreeViewColumn(modPathText, rendererModPath, text=self.moduleColumnPath)
                        columnModPath.set_resizable(True)
                        # show column if running debug
                        if self.runningDebug == True:
                            columnModPath.set_property('visible', True)
                        else:
                            columnModPath.set_property('visible', False)
                        view.append_column(columnModPath)
                        #self.builder.get_object("scrolledwindowModules1").add(view)
                        view.show()
                        # expand Software section
                        view.expand_to_path(Gtk.TreePath.new_from_string('0'))
                        self.setDefaultCursor()

    def addModule(self, modulePath, updating=False):
        try:
            # if not updating, copy to modules dir
            if updating == False:
                r, ext = os.path.splitext(modulePath)
                if ext == '.rmod':
                    installText = _('Installing Module: ')
                    print(installText + os.path.basename(modulePath))
                    shutil.copy(modulePath, self.moduleDir)
                    subprocess.getoutput('chmod -R 777 \"' + self.moduleDir + '\"')
                    # parse and add module to model

                    modPath = os.path.join(self.moduleDir, r)

                    # Refactoring! triplem
                    modProps = self.getModuleProperties(os.path.basename(modulePath))
                    modSubCategory = modProps[self.modSubCategoryKey]

                    if self.modules.has_key(modProps[self.modNameKey]):
                        print("The module is already present")

                    if modSubCategory == 'Administration':
                        iter = self.treeModel.insert_before(self.iterCategoryAdministration, None)
                    elif modSubCategory == 'Education':
                        iter = self.treeModel.insert_before(self.iterCategoryEducation, None)
                    elif modSubCategory == 'Servers':
                        iter = self.treeModel.insert_before(self.iterCategoryServers, None)
                    elif modSubCategory == 'Graphics':
                        iter = self.treeModel.insert_before(self.iterCategoryGraphics, None)
                    elif modSubCategory == 'Multimedia':
                        iter = self.treeModel.insert_before(self.iterCategoryMultimedia, None)
                    elif modSubCategory == 'Networking':
                        iter = self.treeModel.insert_before(self.iterCategoryNetworking, None)
                    elif modSubCategory == 'Plugins':
                        iter = self.treeModel.insert_before(self.iterCategoryPlugins, None)
                    elif modSubCategory == 'Productivity':
                        iter = self.treeModel.insert_before(self.iterCategoryProductivity, None)
                    elif modSubCategory == 'Virtualization':
                        iter = self.treeModel.insert_before(self.iterCategoryVirtualization, None)
                    else:
                        iter = self.treeModel.insert_before(self.iterCategoryMisc, None)

                    self.treeModel.set_value(iter, self.moduleColumnExecute, False)
                    self.treeModel.set_value(iter, self.moduleColumnRunOnBoot, False)
                    self.treeModel.set_value(iter, self.moduleColumnName, modProps[self.modNameKey])
                    self.treeModel.set_value(iter, self.moduleColumnVersion, modProps[self.modVersionKey])
                    self.treeModel.set_value(iter, self.moduleColumnAuthor, modProps[self.modAuthorKey])
                    self.treeModel.set_value(iter, self.moduleColumnDescription, modProps[self.modDescriptionKey])
                    self.treeModel.set_value(iter, self.moduleColumnRunInChroot, bool(modProps[self.modRunInChrootKey]))
                    self.treeModel.set_value(iter, self.moduleColumnUpdateUrl, modProps[self.modUpdateUrlKey])
                    self.treeModel.set_value(iter, self.moduleColumnPath, modPath)

        except Exception as detail:
            errText = _('Error installing module: ')
            print(errText, modulePath + ': ', detail)

    def updateModule(self, moduleName, moduleVersion, moduleFullPath, moduleUpdateUrl, treeview):
        try:
            selection = treeview.get_selection()
            model, iter = selection.get_selected()

            # check for update url
            if moduleUpdateUrl == '':
                updTxt = _('Updating not available for module: ')
                print(updTxt, moduleName)
            # check for updates
            else:
                updTxt = _('Checking updates for module: ')
                print(updTxt, moduleName + '...')
                urllib.urlretrieve(moduleUpdateUrl + os.path.basename(moduleFullPath), "/tmp/r-mod-update.tmp")
                if os.path.exists('/tmp/r-mod-update.tmp'):
                    f = open('/tmp/r-mod-update.tmp', 'r')

                    # Refactoring! triplem
                    newModProps = self.getModuleProperties('/tmp/r-mod-update.tmp')
                    newModSubCategory = newModProps[self.modSubCategoryKey]

                    # check for valid update
                    if newModProps[self.modNameKey] != '':
                        fModVer = float(moduleVersion)
                        fModNewVer = float(newModProps[self.modVersionKey])
                        #print(('Current Module Version: ' + str(fModVer) + ' -- Available: ' + str(fModNewVer)))
                        if fModNewVer > fModVer:
                            # update module
                            verTxt = _('Found new version: ')
                            # prompt for installation
                            updateDlg = Gtk.Dialog(title="Module Update", parent=None, flags=0)
                            updateDlg.add_buttons(Gtk.STOCK_NO, Gtk.RESPONSE_NO, Gtk.STOCK_YES, Gtk.ResponseType.OK)
                            updateDlg.set_icon_from_file(self.iconFile)
                            updateDlg.vbox.set_spacing(10)
                            labelSpc = Gtk.Label()
                            updateDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                            labelSpc.show()
                            # module name label
                            lblModName = Gtk.Label()
                            lblModName.set_text('Reconstructor Module: ' + '<b>' + moduleName + '</b>')
                            lblModName.set_use_markup(True)
                            updateDlg.vbox.pack_start(lblModName, expand=True, fill=True, padding=0)
                            lblModName.show()
                            # module author label
                            lblModAuthor = Gtk.Label()
                            lblModAuthor.set_text('Author: ' + newModProps[self.modAuthorKey])
                            lblModAuthor.set_use_markup(True)
                            updateDlg.vbox.pack_start(lblModAuthor, expand=True, fill=True, padding=0)
                            lblModAuthor.show()
                            # module version label
                            lblNewVersionTxt = _('New version available: ')
                            lblNewVersion = Gtk.Label()
                            lblNowVersion.set_text(lblNewVersionTxt + '<b>' + newModProps[self.modVersionKey] + '</b>')
                            lblNewVersion.set_use_markup(True)
                            updateDlg.vbox.pack_start(lblNewVersion, expand=True, fill=True, padding=0)
                            lblNewVersion.show()
                            #lblInfo = Gtk.Label(updateInfo)
                            #lblInfo.set_use_markup(True)
                            #updateDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
                            #lblInfo.show()
                            lblConfirm = Gtk.Label()
                            lblConfirm.set_text('Update?')
                            updateDlg.vbox.pack_start(lblConfirm, expand=True, fill=True, padding=0)
                            lblConfirm.show()

                            response = updateDlg.run()
                            if response == Gtk.ResponseType.OK:
                                updateDlg.destroy()
                                updateText = _('Updating...')
                                print(updateText)
                                # copy update to modules
                                subprocess.getoutput('cp -Rf /tmp/r-mod-update.tmp ' + '\"' + os.path.join(self.moduleDir, os.path.basename(moduleFullPath)) + '"')
                                # remove old from treemodel
                                self.treeModel.remove(iter)
                                # add new version to treemodel
                                self.addModule(moduleFullPath, updating=True)
                                modUpdatedTxt = _('Module updated.')
                                print(modUpdatedTxt)
                            else:
                                print(_('Module update cancelled.'))
                                updateDlg.destroy()
                        else:
                            # latest version
                            print(_('Module is at the latest version.'))
                    else:
                        errUpdTxt = _('Could not find a valid update for module: ')
                        print(errUpdTxt, moduleName)
                else:
                    print('Updating not available...')
            # cleanup
            if os.path.exists('/tmp/r-mod-update.tmp'):
                subprocess.getoutput('rm -f /tmp/r-mod-update.tmp')
            # set default cursor
            self.setDefaultCursor()

        except Exception as detail:
            # cleanup
            #if os.path.exists('/tmp/r-mod-update.tmp'):
            #    subprocess.getoutput('rm -f /tmp/r-mod-update.tmp')
            # set default cursor
            self.setDefaultCursor()
            errText = _('Error updating module: ')
            print(errText, detail)


    def updateSelectedModule(self):
        try:
            selection = self.treeView.get_selection()
            model, iter = selection.get_selected()
            modName = ''
            modVersion = ''
            modPath = None
            modUpdateUrl = ''
            if iter:
                path = model.get_path(iter)
                modName = model.get_value(iter, self.moduleColumnName)
                modVersion = model.get_value(iter, self.moduleColumnVersion)
                modPath = model.get_value(iter, self.moduleColumnPath)
                modUpdateUrl = model.get_value(iter, self.moduleColumnUpdateUrl)

            # check for valid module and update
            if modPath != None:
                mTxt = _('Checking updates for module: ')
                print(mTxt, modName)
                print(modUpdateUrl + os.path.basename(modPath))
                urllib.urlretrieve(modUpdateUrl + os.path.basename(modPath), "/tmp/r-mod-update.tmp")
                if os.path.exists('/tmp/r-mod-update.tmp'):
                    f = open('/tmp/r-mod-update.tmp', 'r')
                    # parse module and get info
                    newModCategory = ''
                    newModSubCategory = ''
                    newModName = ''
                    newModVersion = ''
                    newModAuthor = ''
                    newModDescription = ''
                    newModRunInChroot = None
                    newModUpdateUrl = ''
                    newModPath = os.path.join(self.moduleDir, os.path.basename(modPath))
                    # HACK: regex through module to get info
                    reModCategory = re.compile(self.regexModCategory, re.IGNORECASE)
                    reModSubCategory = re.compile(self.regexModSubCategory, re.IGNORECASE)
                    reModName = re.compile(self.regexModName, re.IGNORECASE)
                    reModVersion = re.compile(self.regexModVersion, re.IGNORECASE)
                    reModAuthor = re.compile(self.regexModAuthor, re.IGNORECASE)
                    reModDescription = re.compile(self.regexModDescription, re.IGNORECASE)
                    reModRunInChroot = re.compile(self.regexModRunInChroot, re.IGNORECASE)
                    reModUpdateUrl = re.compile(self.regexModUpdateUrl, re.IGNORECASE)

                    for line in fMod:
                        if reModCategory.match(line) != None:
                            newModCategory = reModCategory.match(line).group(1)
                        if reModSubCategory.match(line) != None:
                            newModSubCategory = reModSubCategory.match(line).group(1)
                        if reModName.match(line) != None:
                            newModName = reModName.match(line).group(1)
                        if reModVersion.match(line) != None:
                            newModVersion = reModVersion.match(line).group(1)
                        if reModAuthor.match(line) != None:
                            newModAuthor = reModAuthor.match(line).group(1)
                        if reModDescription.match(line) != None:
                            newModDescription = reModDescription.match(line).group(1)
                        if reModRunInChroot.match(line) != None:
                            newModRunInChroot = reModRunInChroot.match(line).group(1)
                        if reModUpdateUrl.match(line) != None:
                            newModUpdateUrl = reModUpdateUrl.match(line).group(1)
                    f.close()
                    fModVer = float(modVersion)
                    fModNewVer = float(newModVersion)
                    print(('Current Module Version: ' + str(fModVer) + ' -- Available: ' + str(fModNewVer)))
                    if fUpdate > fApp:
                        # update module
                        updateText = _('Updating Module: ')
                        print(updateText, modName + '...')
                    else:
                        # latest version
                        print(_('Module is at the latest version.\n'))
                    # cleanup
                    if os.path.exists('/tmp/r-mod-update.tmp'):
                        subprocess.getoutput('rm -f /tmp/r-mod-update.tmp')
                # set default cursor
                self.setDefaultCursor()

        except Exception as detail:
            errText = _('Error updating module: ')
            print(errText, detail)





    def on_treeitemExecute_toggled(self, cell, path_str, model):
            # get toggled iter
            iter = model.get_iter_from_string(path_str)
            toggle_item = cell.get_active()

            # change value
            toggle_item = not toggle_item

            # clear run on boot if enabled
            if model.get_value(iter, self.moduleColumnRunOnBoot) == True:
                # set to false
                model.set(iter, self.moduleColumnRunOnBoot, False)

            # set new value
            model.set(iter, self.moduleColumnExecute, toggle_item)

            # toggle all child nodes
            if model.iter_n_children(iter) > 0:
                for i in range(model.iter_n_children(iter)):
                    childToggled = model.get_value(model.iter_nth_child(iter, i), self.moduleColumnExecute)
                    model.set(model.iter_nth_child(iter, i), self.moduleColumnExecute, toggle_item)

    def on_treeitemRunOnBoot_toggled(self, cell, path_str, model):
            # get toggled iter
            iter = model.get_iter_from_string(path_str)
            toggle_item = cell.get_active()

            # change value
            toggle_item = not toggle_item

            # clear execute if enabled
            if model.get_value(iter, self.moduleColumnExecute) == True:
                # set to false
                model.set(iter, self.moduleColumnExecute, False)

            # set new value
            model.set(iter, self.moduleColumnRunOnBoot, toggle_item)

            # toggle all child nodes
            if model.iter_n_children(iter) > 0:
                for i in range(model.iter_n_children(iter)):
                    model.set(model.iter_nth_child(iter, i), self.moduleColumnRunOnBoot, toggle_item)

    def on_treeitem_row_activated(self, treeview, path, column):
        self.showModuleSource(treeview)

    def showModuleSource(self, treeview):
        try:
            selection = treeview.get_selection()
            model, iter = selection.get_selected()
            modName = ''
            modPath = None
            if iter:
                path = model.get_path(iter)
                modName = model.get_value(iter, self.moduleColumnName)
                modPath = model.get_value(iter, self.moduleColumnPath)

            if modPath:
                f = open(modPath, 'r')
                scr = f.read()
                f.close()
                # create dialog
                modDlg = Gtk.Dialog(title="Module:  " + modName, parent=None, flags=0)
                modDlg.add_buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.OK)

                modDlg.set_default_size(512, 512)
                modDlg.set_icon_from_file(self.iconFile)
                modDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                modDlg.vbox.pack_start(labelSpc, expand=False, fill=False, padding=0)
                labelSpc.show()
                # scrolled window for module text
                sw = Gtk.ScrolledWindow()
                sw.set_policy(Gtk.POLICY_AUTOMATIC, Gtk.POLICY_AUTOMATIC)
                sw.set_shadow_type(Gtk.SHADOW_IN)
                # text buffer for module
                tBuffer = Gtk.TextBuffer()
                tBuffer.set_text(scr)
                textviewModule = Gtk.TextView(tBuffer)
                textviewModule.set_editable(False)
                sw.add(textviewModule)
                modDlg.vbox.pack_start(sw, expand=True, fill=True, padding=0)

                textviewModule.show()
                sw.show()
                #modDlg.show()
                response = modDlg.run()
                if response != None:
                    modDlg.destroy()


        except Exception as detail:
            print(detail)
            pass

    def copyExecuteModule(self, model, path, iter):
        modName = model.get_value(iter, self.moduleColumnName)
        modExecute = model.get_value(iter, self.moduleColumnExecute)
        modPath = model.get_value(iter, self.moduleColumnPath)
        modRunInChroot = model.get_value(iter, self.moduleColumnRunInChroot)
        # check for module and skip category
        if modPath != None:
            # check for execute
            if modExecute == True:
                #print(modName, modRunInChroot)
                if modRunInChroot == True:
                    #print(modName + ' - Running in chroot...')
                    subprocess.getoutput('cp -R \"' + modPath + '\" \"' + os.path.join(self.customDir, "root/tmp/") + '\"')
                    subprocess.getoutput('chmod a+x \"' + os.path.join(self.customDir, "root/tmp/") + os.path.basename(modPath) + '\"')

                else:
                    print(modName + ' - Running in custom directory...')
                    subprocess.getoutput('cp -R \"' + modPath + '\" \"' + self.customDir + '\"')
                    subprocess.getoutput('chmod a+x \"' + os.path.join(self.customDir, os.path.basename(modPath)) + '\"')

    def copyRunOnBootModule(self, model, path, iter):
        modName = model.get_value(iter, self.moduleColumnName)
        modRunOnBoot = model.get_value(iter, self.moduleColumnRunOnBoot)
        modPath = model.get_value(iter, self.moduleColumnPath)
        # check for module and skip category
        if modPath != None:
            # check for run on boot
            if modRunOnBoot == True:
                # check for script dir
                if os.path.exists(os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/")) == False:
                    subprocess.getoutput('mkdir -p \"' + os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/") + '\"')
                # copy module
                subprocess.getoutput('cp -R \"' + modPath + '\" \"' + os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/") + '\"')
                subprocess.getoutput('chmod a+x \"' + os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/") + os.path.basename(modPath) + '\"')
                txt = _('Copied module: ')
                print(txt, modName)

    def checkExecModuleEnabled(self, model, path, iter):
        modExecute = model.get_value(iter, self.moduleColumnExecute)
        if modExecute == True:
            self.execModulesEnabled = True

    def checkBootModuleEnabled(self, model, path, iter):
        modRunOnBoot = model.get_value(iter, self.moduleColumnRunOnBoot)
        if modRunOnBoot == True:
            self.bootModulesEnabled = True

    def clearRunOnBootModules(self):
        try:
            # remove all run on boot modules and scripts
            print(_('Clearing all run on boot modules and scripts...'))
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/skel/.gnomerc") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/usr/share/reconstructor/") + '\"')
        except Exception as detail:
            errText = _('Error clearing run on boot modules: ')
            print(errText, detail)

    def checkSetup(self):
        setup = False
        if self.createRemasterDir == True:
            setup = True
        elif self.createCustomRoot == True:
            setup = True
        elif self.createInitrdRoot == True:
            setup = True
        else:
            # nothing to be done
            setup = False
        return setup

    def checkAltSetup(self):
        setup = False
        if self.createAltRemasterDir == True:
            setup = True
        elif self.createAltInitrdRoot == True:
            setup = True
        else:
            # nothing to be done
            setup = False
        return setup

    def checkCustomDir(self):
        if self.customDir == "":
            return False
        else:
            if os.path.exists(self.customDir) == False:
                os.makedirs(self.customDir)
            return True

    def setPage(self, pageNum):
        self.builder.get_object("notebookWizard").set_current_page(pageNum)

    def setBusyCursor(self):
        self.working = True
        self.builder.get_object("windowMain").get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

    def setDefaultCursor(self):
        self.working = False
        self.builder.get_object("windowMain").get_window().set_cursor(None)

    def showWorking(self):
        self.workingDlg = Gtk.Dialog(title="Working")
        self.workingDlg.set_modal(True)
        self.workingDlg.show()

    def hideWorking(self):
        self.workingDlg.hide()

    def checkWindowsPrograms(self):
        apps = False
        if os.path.exists(os.path.join(self.customDir, "remaster/bin")):
            apps = True
        if os.path.exists(os.path.join(self.customDir, "remaster/programs")):
            apps = True
        if os.path.exists(os.path.join(self.customDir, "remaster/autorun.inf")):
            apps = True
        return apps

    # checks if user entered custom password matches
    def checkUserPassword(self):
        if self.builder.get_object("entryLiveCdUserPassword").get_text() == self.builder.get_object("entryLiveCdUserPasswordCheck").get_text():
            return True
        else:
            return False

    def checkSoftware(self):
        install = False
        # custom apt-get
        if self.builder.get_object("entryCustomAptInstall").get_text() != "":
            install = True
        # software removal
        # custom
        if self.builder.get_object("entryCustomAptRemove").get_text() != "":
            install = True

        return install

    def checkCustomRepos(self):
        customRepos = False
        buf = self.builder.get_object("textviewAptCustomArchives").get_buffer()
        if self.builder.get_object("checkbuttonAptRepoUbuntuOfficial").get_active() == True:
            #print("Selected Ubuntu Official apt archive...")
            customRepos = True
        elif self.builder.get_object("checkbuttonAptRepoUbuntuRestricted").get_active() == True:
            #print("Selected Ubuntu Restricted apt archive...")
            customRepos = True
        elif self.builder.get_object("checkbuttonAptRepoUbuntuUniverse").get_active() == True:
            #print("Selected Ubuntu Universe apt archive...")
            customRepos = True
        elif self.builder.get_object("checkbuttonAptRepoUbuntuMultiverse").get_active() == True:
            #print("Selected Ubuntu Multiverse apt archive...")
            customRepos = True
        elif buf.get_text(buf.get_start_iter(),buf.get_end_iter(), False) != '':
            customRepos = True
        else:
            #print("No custom apt repos.  Using defaults.")
            customRepos = False
        return customRepos

    def checkAltCustomRepos(self):
        customRepos = False
        if self.builder.get_object("checkbuttonAltUbuntuOfficialRepo").get_active() == True:
            #print("Selected Ubuntu Official apt archive...")
            customRepos = True
        elif self.builder.get_object("checkbuttonAltUbuntuRestrictedRepo").get_active() == True:
            #print("Selected Ubuntu Restricted apt archive...")
            customRepos = True
        elif self.builder.get_object("checkbuttonAltUbuntuUniverseRepo").get_active() == True:
            #print("Selected Ubuntu Universe apt archive...")
            customRepos = True
        elif self.builder.get_object("checkbuttonAltUbuntuMultiverseRepo").get_active() == True:
            #print("Selected Ubuntu Multiverse apt archive...")
            customRepos = True
        else:
            #print("No custom apt repos.  Using defaults.")
            customRepos = False
        return customRepos

    def checkCustomGdm(self):
        customGdm = False
        if self.builder.get_object("comboboxentryGnomeGdmTheme").get_active_id() != "" \
              and self.builder.get_object("comboboxentryGnomeGdmTheme").get_active_id() != None:
            customGdm = True
        if self.builder.get_object("checkbuttonGdmSounds").get_active() == True:
            customGdm = True
        if self.builder.get_object("checkbuttonGdmRootLogin").get_active() == True:
            customGdm = True
        if self.builder.get_object("checkbuttonGdmXdmcp").get_active() == True:
            customGdm = True
        color = self.builder.get_object("colorbuttonBrowseGdmBackgroundColor").get_rgba().to_color()
        rgbColor = color.red//255, color.green//255, color.blue//255
        hexColor = '%02x%02x%02x' % rgbColor
        if self.gdmBackgroundColor != str(hexColor):
            customGdm = True
        return customGdm

    def checkWorkingDir(self):
        # check for existing directories; if not warn...
        remasterExists = None
        rootExists = None
        initrdExists = None
        if os.path.exists(os.path.join(self.customDir, "remaster")) == False:
            if self.builder.get_object("checkbuttonCreateRemaster").get_active() == False:
                remasterExists = False
        if os.path.exists(os.path.join(self.customDir, "root")) == False:
            if self.builder.get_object("checkbuttonCreateRoot").get_active() == False:
                rootExists = False
        if os.path.exists(os.path.join(self.customDir, "initrd")) == False:
            if self.builder.get_object("checkbuttonCreateInitRd").get_active() == False:
                initrdExists = False
        workingDirOk = True
        if remasterExists == False:
            workingDirOk = False
        if rootExists == False:
            workingDirOk = False
        if initrdExists == False:
            workingDirOk = False
        if workingDirOk == False:
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label()
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblWarningText = _("  <b>Please fix the errors below before continuing.</b>   ")
            lblRemasterText = _("  There is no remaster directory.  Please select create remaster option.  ")
            lblRootText = _("  There is no root directory.  Please select create root option.  ")
            lblInitrdText = _("  There is no initrd directory.  Please select create initrd option.  ")
            labelWarning = Gtk.Label()
            labelWarning.set_text(lblWarningText)
            labelRemaster = Gtk.Label()
            labelRemaster.set_text(lblRemasterText)
            labelRoot = Gtk.Label()
            labelRoot.set_text(lblRootText)
            labelInitrd = Gtk.Label()
            labelInitrd.set_text(lblInitrdText)

            labelWarning.set_use_markup(True)
            labelRemaster.set_use_markup(True)
            labelRoot.set_use_markup(True)
            labelInitrd.set_use_markup(True)
            warnDlg.vbox.pack_start(labelWarning, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(labelRemaster, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(labelRoot, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(labelInitrd, expand=True, fill=True, padding=0)
            labelWarning.show()

            if remasterExists == False:
                labelRemaster.show()
            if rootExists == False:
                labelRoot.show()
            if initrdExists == False:
                labelInitrd.show()

            #warnDlg.show()
            response = warnDlg.run()
            # HACK: return False no matter what
            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
            else:
                warnDlg.destroy()
        return workingDirOk

    def checkAltWorkingDir(self):
        # check for existing directories; if not warn...
        remasterExists = None
        initrdExists = None
        if os.path.exists(os.path.join(self.customDir, self.altRemasterDir)) == False:
            if self.builder.get_object("checkbuttonAltCreateRemasterDir").get_active() == False:
                remasterExists = False
        if os.path.exists(os.path.join(self.customDir, self.altInitrdRoot)) == False:
            if self.builder.get_object("checkbuttonAltCreateInitrdDir").get_active() == False:
                initrdExists = False
        workingDirOk = True
        if remasterExists == False:
            workingDirOk = False
        if initrdExists == False:
            workingDirOk = False
        if workingDirOk == False:
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label()
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblWarningText = _("  <b>Please fix the errors below before continuing.</b>   ")
            lblRemasterText = _("  There is no remaster directory.  Please select create remaster option.  ")
            lblInitrdText = _("  There is no initrd directory.  Please select create initrd option.  ")
            labelWarning = Gtk.Label()
            labelWarning.set_text(lblWarningText)
            labelRemaster = Gtk.Label()
            labelRemaster.set_text(lblRemasterText)
            labelInitrd = Gtk.Label()
            labelInitrd.set_text(lblInitrdText)

            labelWarning.set_use_markup(True)
            labelRemaster.set_use_markup(True)
            labelInitrd.set_use_markup(True)
            warnDlg.vbox.pack_start(labelWarning, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(labelRemaster, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(labelInitrd, expand=True, fill=True, padding=0)
            labelWarning.show()

            if remasterExists == False:
                labelRemaster.show()
            if initrdExists == False:
                labelInitrd.show()

            #warnDlg.show()
            response = warnDlg.run()
            # HACK: return False no matter what
            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
            else:
                warnDlg.destroy()
        return workingDirOk

    def readConfig(self):
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(os.path.join(self.customDir, ".reconstructor.conf"))
        if not config.has_section('global'):
            config.add_section('global')
        if not config.has_section('ISO'):
            config.add_section('ISO')

        try:
            discType = config.get('ISO','discType')
        except:
            discType = 'live'

        if discType == self.discType:
            if discType == 'live':
                try:
                    self.buildLiveCdFilename = config.get('ISO','isofilename')
                except:
                    self.buildLiveCdFilename = ''
            else:
                try:
                    self.buildAltCdFilename = config.get('ISO','isofilename')
                except:
                    self.buildaltCdFilename = ''

            try:
                self.cdDesc = config.get('ISO','cddesc')
            except:
                self.cdDesc = ''

            try:
                self.cdArchIndex = int(config.get('ISO','cdarchidx'))
            except:
                self.cdArchIndex = 0

    def saveConfig(self):
        config = configparser.ConfigParser()
        config.optionxform = str
        if not config.has_section('global'):
            config.add_section('global')
        config.set('global','workdir',self.customDir)
        config.write(open(os.path.join(os.environ['HOME'], ".reconstructor"),'wt'))
        config.remove_section('global')

        if not config.has_section('ISO'):
            config.add_section('ISO')
        config.set('ISO','discType',self.discType)
        if self.discType == 'live':
            config.set('ISO','isofilename',self.builder.get_object("entryLiveIsoFilename").get_text())
            config.set('ISO','cddesc',self.builder.get_object("entryLiveCdDescription").get_text())
            config.set('ISO','cdarchidx',str(self.builder.get_object("comboboxLiveCdArch").get_active()))
        else:
            config.set('ISO','isofilename',self.builder.get_object("entryAltIsoFilename").get_text())
            config.set('ISO','cddesc',self.builder.get_object("entryAltCdDescription").get_text())
            config.set('ISO','cdarchidx',str(self.builder.get_object("comboboxAltCdArch").get_active()))
        config.write(open(os.path.join(self.customDir, ".reconstructor.conf"),'wt'))


    def checkPage(self, pageNum):
        if self.runningDebug == True:
            print("CheckPage: " + str(pageNum))
            #print(" ")
        if pageNum == self.pageWelcome:
            # intro
            if self.customDir:
                self.builder.get_object("entryWorkingDir").set_text(self.customDir)
            self.setPage(self.pageDiscType)
            return True
        elif pageNum == self.pageDiscType:
            typeText = _("Disc Type:")
            # continue based on disc type (live/alt)
            if self.builder.get_object("radiobuttonDiscTypeLive").get_active() == True:
                # set disc type
                self.discType = "live"
                print(typeText, " " + self.discType)
                self.setPage(self.pageLiveSetup)
            elif self.builder.get_object("radiobuttonDiscTypeAlt").get_active() == True:
                # set disc type
                self.discType = "alt"
                print(typeText, " " + self.discType)
                self.setPage(self.pageAltSetup)
            else:
                print(typeText, " is None")
        elif pageNum == self.pageLiveSetup:
            # setup
            self.saveSetupInfo()
            # reset interactive edit
            self.interactiveEdit = False
            # check for custom dir
            if self.checkCustomDir() == True:
                self.readConfig()
                self.doneTerminal(forceMode=True,silentMode=False,justUmount=True)
                if self.checkSetup() == True:
                    if self.checkWorkingDir() == True:
                        warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                        warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
                        warnDlg.set_icon_from_file(self.iconFile)
                        warnDlg.vbox.set_spacing(10)
                        labelSpc = Gtk.Label()
                        warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                        labelSpc.show()
                        lblContinueText = _("  <b>Continue?</b>  ")
                        lblContinueInfo = _("     This may take a few minutes.  Please wait...     ")
                        label = Gtk.Label()
                        label.set_text(lblContinueText)
                        lblInfo = Gtk.Label()
                        lblInfo.set_text(lblContinueInfo)
                        label.set_use_markup(True)
                        warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                        warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
                        lblInfo.show()
                        label.show()
                        #warnDlg.show()
                        response = warnDlg.run()
                        if response == Gtk.ResponseType.OK:
                            warnDlg.destroy()
                            self.setBusyCursor()
                            self.run_generator(self.setupWorkingDirectory)
                            # load modules
                            GLib.idle_add(self.loadModules)
                            self.setBusyCursor()
                            return True
                        else:
                            warnDlg.destroy()
                            return False
                    else:
                        return False
                else:
                    if self.checkWorkingDir() == True:
                        # get ubuntu version
                        self.loadCdVersion()
                        if apt_pkg.version_compare(self.cdUbuntuVersion, '14.04') >= 0:
                            self.builder.get_object("notebookCustomize").hide()
                            self.builder.get_object("vboxCustomizeLive").show()
                        else:
                            self.builder.get_object("notebookCustomize").show()
                            self.builder.get_object("vboxCustomizeLive").hide()
                            # get current boot options menu text color
                            self.loadBootMenuColor()
                        # load desktop environments
                        self.setBusyCursor()
                        # load modules
                        #GLib.idle_add(self.loadModules)

                        self.checkChroot()

                        # calculate iso size in the background
                        self.run_generator(self.calculateIsoSize)
                        #self.calculateIsoSize()
                        return True
                    else:
                        return False
            else:
                warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                warnDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
                warnDlg.set_icon_from_file(self.iconFile)
                warnDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label()
                warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblWorkingDirText = _("  <b>You must enter a working directory.</b>  ")
                label = Gtk.Label()
                label.set_text(lblWorkingDirText)
                #lblInfo = Gtk.Label("     This may take a few minutes.  Please     wait...     ")
                label.set_use_markup(True)
                warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                #warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
                #lblInfo.show()
                label.show()
                #warnDlg.show()
                response = warnDlg.run()
                # HACK: return False no matter what
                if response == Gtk.ResponseType.OK:
                    warnDlg.destroy()
                    return False
                else:
                    warnDlg.destroy()
                    return False
        elif pageNum == self.pageLiveCustomize:
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label()
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblContinueText = _("  <b>Continue?</b>  ")
            label = Gtk.Label()
            label.set_text(lblContinueText)
            label.set_use_markup(True)
            lblApplyText = _("Be sure to click <b>Apply</b> to apply changes before continuing.")
            lblApply = Gtk.Label()
            lblApply.set_text(lblApplyText)
            lblApply.set_use_markup(True)
            warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(lblApply, expand=True, fill=True, padding=0)
            label.show()
            lblApply.show()
            #warnDlg.show()
            # set iso filenames
            if self.buildLiveCdFilename and self.buildLiveCdFilename != "":
                self.builder.get_object("entryLiveIsoFilename").set_text(self.buildLiveCdFilename)
            # set descriptions
            if self.cdDesc and self.cdDesc != "":
                self.builder.get_object("entryLiveCdDescription").set_text(self.cdDesc)

            self.builder.get_object("comboboxLiveCdArch").set_active(self.cdArchIndex)

            response = warnDlg.run()
            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
                self.doneTerminal(forceMode=False,silentMode=False,justUmount=False)
                self.showProgress('Customized Live CD.',0.50)

                self.setPage(self.pageLiveBuild)
                # check for windows apps and enable/disable checkbox as necessary
                if self.checkWindowsPrograms() == True:
                    self.builder.get_object("checkbuttonLiveCdRemoveWin32Programs").set_sensitive(True)
                else:
                    self.builder.get_object("checkbuttonLiveCdRemoveWin32Programs").set_sensitive(False)
                # HACK: check in case "create iso" option is unchecked
                # enable/disable iso burn
                self.checkEnableBurnIso()
                return True
            else:
                warnDlg.destroy()
                return False

        elif pageNum == self.pageLiveBuild:
            #write config 
            self.saveConfig()

            # build
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label()
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblBuildText = _("  <b>Build Live CD?</b>  ")
            lblBuildInfo = _("     This may take a few minutes.  Please wait...     ")
            label = Gtk.Label()
            label.set_text(lblBuildText)
            lblInfo = Gtk.Label()
            lblInfo.set_text(lblBuildInfo)
            label.set_use_markup(True)
            warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
            lblInfo.show()
            label.show()
            #warnDlg.show()

            response = warnDlg.run()
            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
                self.setBusyCursor()
                self.doneTerminal(forceMode=True,silentMode=False,justUmount=False)
                self.run_generator(self.build)
                # change Next text to Finish
                self.builder.get_object("buttonNext").set_label("Finish")
                return True
            else:
                warnDlg.destroy()
                return False

        elif pageNum == self.pageAltSetup:
            # setup
            self.saveAltSetupInfo()
            # check for custom dir
            if self.checkCustomDir() == True:
                self.readConfig()
                if self.checkAltSetup() == True:
                    if self.checkAltWorkingDir() == True:
                        warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                        warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
                        warnDlg.set_icon_from_file(self.iconFile)
                        warnDlg.vbox.set_spacing(10)
                        labelSpc = Gtk.Label()
                        warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                        labelSpc.show()
                        lblContinueText = _("  <b>Continue?</b>  ")
                        lblContinueInfo = _("     This may take a few minutes.  Please wait...     ")
                        label = Gtk.Label()
                        label.set_text(lblContinueText)
                        lblInfo = Gtk.Label()
                        lblInfo.set_text(lblContinueInfo)
                        label.set_use_markup(True)
                        warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                        warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
                        lblInfo.show()
                        label.show()
                        #warnDlg.show()
                        response = warnDlg.run()
                        if response == Gtk.ResponseType.OK:
                            warnDlg.destroy()
                            self.setBusyCursor()
                            self.run_generator(self.setupAltWorkingDirectory)
                            return True
                        else:
                            warnDlg.destroy()
                            return False
                    else:

                        return False
                else:
                    if self.checkAltWorkingDir() == True:
                        self.setBusyCursor()
                        # calculate iso size in the background
                        self.run_generator(self.calculateAltIsoSize)
                        return True
                    else:
                        return False
            else:
                warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                warnDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
                warnDlg.set_icon_from_file(self.iconFile)
                warnDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label()
                warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblWorkingDirText = _("  <b>You must enter a working directory.</b>  ")
                label = Gtk.Label()
                label.set_text(lblWorkingDirText)
                #lblInfo = Gtk.Label("     This may take a few minutes.  Please     wait...     ")
                label.set_use_markup(True)
                warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                #warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
                #lblInfo.show()
                label.show()
                #warnDlg.show()
                response = warnDlg.run()
                # HACK: return False no matter what
                if response == Gtk.ResponseType.OK:
                    warnDlg.destroy()
                    return False
                else:
                    warnDlg.destroy()
                    return False
        elif pageNum == self.pageAltCustomize:
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label()
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblContinueText = _("  <b>Continue?</b>  ")
            label = Gtk.Label()
            label.set_text(lblContinueText)
            label.set_use_markup(True)
            lblApplyText = _("Be sure to click <b>Apply</b> to apply changes before continuing.")
            lblApply = Gtk.Label()
            lblApply.set_text(lblApplyText)
            lblApply.set_use_markup(True)
            warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(lblApply, expand=True, fill=True, padding=0)
            label.show()
            lblApply.show()
            #warnDlg.show()

            # set iso filenames
            if self.buildAltCdFilename and self.buildAltCdFilename != "":
                self.builder.get_object("entryAltIsoFilename").set_text(self.buildAltCdFilename)
            # set descriptions
            if self.cdDesc and self.cdDesc != "":
                self.builder.get_object("entryAltCdDescription").set_text(self.cdDesc)

            self.builder.get_object("comboboxAltBuildArch").set_active(self.cdArchIndex)

            response = warnDlg.run()
            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
                self.showProgress(False,0.60)
                self.setPage(self.pageAltBuild)
                # HACK: check in case "create iso" option is unchecked
                # enable/disable iso burn
                self.checkEnableBurnIso()
                self.showProgress(False,0.70)
                return True
            else:
                warnDlg.destroy()
                return False
        elif pageNum == self.pageAltBuild:
            #write config 
            #write config 
            self.saveConfig()
            # build
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label()
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblBuildText = _("  <b>Build Alternate CD?</b>  ")
            lblBuildInfo = _("     This may take a few minutes.  Please wait...     ")
            label = Gtk.Label()
            label.set_text(lblBuildText)
            lblInfo = Gtk.Label()
            lblInfo.set_text(lblBuildInfo)
            label.set_use_markup(True)
            warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
            lblInfo.show()
            label.show()
            #warnDlg.show()
            response = warnDlg.run()

            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
                self.setBusyCursor()
                self.showProgress(_('Building Alternate CD...'),0.72)
                self.run_generator(self.buildAlternate)
                # change Next text to Finish
                self.builder.get_object("buttonNext").set_label("Finish")
                return True
            else:
                warnDlg.destroy()
                return False

        elif pageNum == self.pageFinish:
            # finished... exit
            print(_("Exiting..."))
            Gtk.main_quit()
            sys.exit(0)

    def checkEnableBurnIso(self):
        # show burn iso button if nautilus-cd-burner exists
        if subprocess.getoutput('which nautilus-cd-burner') != '':
            # make sure iso isn't blank
            if os.path.exists(self.builder.get_object("entryLiveIsoFilename").get_text()):
                self.builder.get_object("buttonBurnIso").show()
            else:
                self.builder.get_object("buttonBurnIso").hide()
        else:
            self.builder.get_object("buttonBurnIso").hide()

    def checkEnableBurnAltIso(self):
        # show burn iso button if nautilus-cd-burner exists
        if subprocess.getoutput('which nautilus-cd-burner') != '':
            # make sure iso isn't blank
            if os.path.exists(self.builder.get_object("entryAltBuildIsoFilename").get_text()):
                self.builder.get_object("buttonBurnIso").show()
            else:
                self.builder.get_object("buttonBurnIso").hide()
        else:
            self.builder.get_object("buttonBurnIso").hide()

    def exitApp(self,widget, data=None):
        self.doneTerminal(forceMode=True,silentMode=False,justUmount=True)
        Gtk.main_quit()
        sys.exit(0)

    # VMWare Player installation
    def installVmwarePlayer(self):
        try:
            print(_("Installing VMWare Player..."))
            # tar archive for install
            vmfile = 'VMware-player-1.0.1-19317.tar.gz'
            # check for previously downloaded archive
            if os.path.exists(os.path.join(self.customDir, "root/tmp/vmware-player.tar.gz")) == False:
                # download file
                print(_("Downloading VMWare Player archive..."))
                # HACK: using wget to download file
                subprocess.getoutput('wget http://download3.vmware.com/software/vmplayer/' + vmfile + ' -O ' + os.path.join(self.customDir, "root/tmp/vmware-player.tar.gz"))
            # extract
            print(_("Extracting VMWare Player archive..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' tar zxf /tmp/vmware-player.tar.gz -C /tmp/ 1>&2 2>/dev/null')
            print(_("Installing dependencies for VMWare Player..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get install --assume-yes --force-yes -d gcc make linux-headers-$(uname -r)')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' dpkg -i -R /var/cache/apt/archives/ 1>&2 2>/dev/null')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get clean')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get autoclean')
            # create symlink /usr/src/linux
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' ln -sf /usr/src/linux-headers-$(uname -r) /usr/src/linux')
            # install (launch xterm for installation/configuration)
            # HACK: write temporary script for chroot & install
            scr = '#!/bin/sh\ncd /tmp/vmware-player-distrib/\n\n/tmp/vmware-player-distrib/vmware-install.pl -d\n'
            f=open(os.path.join(self.customDir, "root/tmp/vmware-player-install.sh"), 'w')
            f.write(scr)
            f.close()
            subprocess.getoutput('chmod a+x ' + os.path.join(self.customDir, "root/tmp/vmware-player-install.sh"))
            subprocess.getoutput('xterm -title \'VMWare Player Installation\' -e chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/vmware-player-install.sh')

            # cleanup if not running debug
            if self.runningDebug == False:
                print(_("Cleaning Up Temporary Files..."))
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/vmware-player-distrib/\"')
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/vmware-player-install.sh\"')
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/vmware-player.tar.gz\"')
        except Exception as detail:
            errText = _('Error installing VMWare Player: ')
            print(errText, detail)
            pass

    # Qemu installation
    def installQemu(self):
        try:
            print(_('Installing Qemu Emulator with KQemu Accelerator module...'))
            qemuFile = 'qemu-0.8.2-i386.tar.gz'
            kqemuFile = 'kqemu-1.3.0pre9.tar.gz'
            kqemuDir = 'kqemu-1.3.0pre9'
            # check for previously downloaded archive
            if os.path.exists(os.path.join(self.customDir, "root/tmp/qemu.tar.gz")) == False:
                # download file
                print(_('Downloading Qemu archive...'))
                # HACK: using wget to download file
                subprocess.getoutput('wget http://fabrice.bellard.free.fr/qemu/' + qemuFile + ' -O ' + os.path.join(self.customDir, "root/tmp/qemu.tar.gz"))
            # check for previously downloaded archive
            if os.path.exists(os.path.join(self.customDir, "root/tmp/kqemu.tar.gz")) == False:
                # download file
                print(_('Downloading KQemu module archive...'))
                # HACK: using wget to download file
                subprocess.getoutput('wget http://fabrice.bellard.free.fr/qemu/' + kqemuFile + ' -O ' + os.path.join(self.customDir, "root/tmp/kqemu.tar.gz"))

            # extract to root dir
            print(_('Extracting Qemu into /usr/local...'))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' tar zxf /tmp/qemu.tar.gz -C / 1>&2 2>/dev/null')
            print(_('Extracting KQemu module...'))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' tar zxf /tmp/kqemu.tar.gz -C /tmp/ 1>&2 2>/dev/null')
            print(_("Installing dependencies for KQemu Compilation..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get install --assume-yes --force-yes -d gcc make linux-headers-$(uname -r)')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' dpkg -i -R /var/cache/apt/archives/ 1>&2 2>/dev/null')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get clean')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get autoclean')
            # create symlink /usr/src/linux
            # compile kqemu
            print(_('Installing KQemu module...'))
            # HACK: write temporary script for chroot & install
            scr = '#!/bin/sh\ncd /tmp/' + kqemuDir + '/\n\n./configure 1>&2 2>/dev/null\n make install\n'
            f=open(os.path.join(self.customDir, "root/tmp/kqemu-install.sh"), 'w')
            f.write(scr)
            f.close()
            subprocess.getoutput('chmod a+x ' + os.path.join(self.customDir, "root/tmp/kqemu-install.sh"))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/kqemu-install.sh')

            # add module load to sys startup
            print(_("Setting KQemu module to load on startup..."))
            modExists = False
            f = open(os.path.join(self.customDir, "root/etc/modules"), 'r')
            lines = []
            r = re.compile('kqemu', re.IGNORECASE)
            # find config string
            for line in f:
                if r.search(line) != None:
                    # mark as found
                    modExists = True
                lines.append(line)

            f.close()
            # rewrite if necessary
            if modExists == False:
                f = open(os.path.join(self.customDir, "root/etc/modules"), 'w')
                f.writelines(lines)
                f.write('kqemu\n')
                f.close()

            # cleanup if not running debug
            if self.runningDebug == False:
                print(_("Cleaning Up Temporary Files..."))
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/*\"')

        except Exception as detail:
            errText = _('Error Installing QEmu: ')
            print(errText, detail)
            pass

    # Java installation
    def installJava(self):
        try:
            print(_('Installing Java...'))
            # HACK: write temporary script for chroot & install
            scr = '#!/bin/sh\napt-get install -y j2re1.4\napt-get clean\napt-get autoclean\nsleep 3\n'
            f=open(os.path.join(self.customDir, "root/tmp/java-install.sh"), 'w')
            f.write(scr)
            f.close()
            subprocess.getoutput('chmod a+x ' + os.path.join(self.customDir, "root/tmp/java-install.sh"))
            subprocess.getoutput('xterm -title \'Java Installation\' -e chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/java-install.sh')
            # cleanup
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/java-install.sh\"')

        except Exception as detail:
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/java-install.sh\"')
            errText = _('Error installing Java: ')
            print(errText, detail)
            pass

    # Flash installation
    def installFlash(self):
        try:
            print(_('Installing Flash...'))
            # HACK: write temporary script for chroot & install
            scr = '#!/bin/sh\napt-get install -y flashplugin-nonfree\napt-get clean\napt-get autoclean\nsleep 3\n'
            f=open(os.path.join(self.customDir, "root/tmp/flash-install.sh"), 'w')
            f.write(scr)
            f.close()
            subprocess.getoutput('chmod a+x ' + os.path.join(self.customDir, "root/tmp/flash-install.sh"))
            subprocess.getoutput('xterm -title \'Flash Installation\' -e chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/flash-install.sh')
            # cleanup
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/flash-install.sh\"')

        except Exception as detail:
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + 'tmp/flash-install.sh\"')
            errText = _('Error installing Flash: ')
            print(errText, detail)
            pass


    # launch chroot terminal
    def launchTerminal(self):
        try:
            if self.TerminalInitialized == False:
                # setup environment
                # add current user to the access control list
                user = subprocess.getoutput('echo $USER')
                print(_("Adding user " + user + " to access control list..."))
                subprocess.getoutput('xhost +local:' + user)
                # copy dns info
                #if os.path.exists(os.path.join(self.customDir, "root/etc/resolv.conf")):
                if os.path.exists("/etc/resolv.conf"):
                    print(_("Copying DNS info..."))
                    subprocess.getoutput('cp -L --remove-destination /etc/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
                elif os.path.exists("/run/resolvconf/resolv.conf"):
                    print(_("Copying DNS info..."))
                    subprocess.getoutput('cp -L --remove-destination /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
                #mount /run/dbus
                print(_("Mounting /run/dbus filesystem..."))
                if not os.path.exists(os.path.join(self.customDir, "root/run/dbus")):
                    subprocess.getoutput("mkdir " + (os.path.join(self.customDir, "root/run/dbus")))
                subprocess.getoutput('mount --bind /run/dbus \"' + os.path.join(self.customDir, "root/run/dbus") + '\"')
                #mount /dev
                print(_("Mounting /dev filesystem..."))
                subprocess.getoutput('mount --bind /dev \"' + os.path.join(self.customDir, "root/dev") + '\"')
                # mount /proc
                print(_("Mounting /proc filesystem..."))
                subprocess.getoutput('mount none -t proc \"' + os.path.join(self.customDir, "root/proc") + '\"')
                #mount /sys
                print(_("Mounting /sys filesystem..."))
                subprocess.getoutput('mount none -t sysfs \"' + os.path.join(self.customDir, "root/sys") + '\"')
                #mount /dev/pts
                print(_("Mounting /dev/pts filesystem..."))
                subprocess.getoutput('mount none -t devpts \"' + os.path.join(self.customDir, "root/dev/pts") + '\"')
                # copy apt.conf
                print(_("Copying apt configuration..."))
                if not os.path.exists(os.path.join(self.customDir, "root/etc/apt/apt.conf.d/")):
                    os.makedirs(os.path.join(self.customDir, "root/etc/apt/apt.conf.d/"))
                subprocess.getoutput('cp -f /etc/apt/apt.conf.d/* ' + os.path.join(self.customDir, "root/etc/apt/apt.conf.d/"))
                # copy wgetrc
                print(_("Copying wgetrc configuration..."))
                # backup
                subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\"')
                subprocess.getoutput('cp -f /etc/wgetrc ' + os.path.join(self.customDir, "root/etc/wgetrc"))
                # HACK: create temporary script for chrooting
                scr = '#!/bin/bash\n#\n#\t(c) reconstructor, 2006\n#\nchroot ' + os.path.join(self.customDir, "root/") + '\n'
                f=open('/tmp/reconstructor-terminal.sh', 'w')
                f.write(scr)
                f.close()
                subprocess.getoutput('chmod a+x ' + os.path.join(self.customDir, "/tmp/reconstructor-terminal.sh"))
                self.TerminalInitialized = True
            # TODO: replace default terminal title with "Reconstructor Terminal"
            # use COLORTERM if available -- more features
            # get COLORTERM
            terminal = self.getTerminal()
            if terminal != '' and subprocess.getoutput('which '+ terminal) != '':
                print(_('Launching ' + terminal +' for advanced customization...'))
                subprocess.getoutput('export HOME=/root ; ' + terminal + ' --hide-menubar -t \"Reconstructor Terminal\" -e \"/tmp/reconstructor-terminal.sh\" >/tmp/terminal-reconstructor.log')
                if subprocess.getoutput('cat /tmp/terminal-reconstructor.log | grep fail') != '':
                    print(_(failed + '\nLaunching Xterm for advanced customization...'))
                    subprocess.getoutput('export HOME=/root ; xterm -bg black -fg white -rightbar -title \"Reconstructor Terminal\" -e /tmp/reconstructor-terminal.sh')
                subprocess.getoutput('rm -f /tmp/terminal-reconstructor.log')
            else:
                print(_('Launching Xterm for advanced customization...'))
                # use xterm if COLORTERM isn't available
                subprocess.getoutput('export HOME=/root ; xterm -bg black -fg white -rightbar -title \"Reconstructor Terminal\" -e /tmp/reconstructor-terminal.sh')
        except Exception as detail:
            self.doneTerminal(forceMode=True,silentMode=False,justUmount=False)
            errText = _('Error launching terminal: ')
            print(errText, detail)
            pass

        return

    def doneTerminal(self,forceMode=False,silentMode=False,justUmount=False):
            if self.customDir != '' and ( self.TerminalInitialized == True or forceMode == True ):
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/var/lib/dpkg/lock"))   
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/var/lib/apt/lists/lock"))   
                # umount /proc
                if self.isMounted(os.path.join(self.customDir, "root/proc")):
                    if silentMode == False:
                        print(_("Umounting /proc..."))
                    error = subprocess.getoutput('umount  -lf \"' + os.path.join(self.customDir, "root/proc") + '\"')
                    if(error != ''):
                        print("error=\""+error+"\"")
                        self.suggestReboot('/proc could not be unmounted. It must be unmounted before you can build an ISO.')
                # umount /sys
                if self.isMounted(os.path.join(self.customDir, "root/sys")):
                    if silentMode == False:
                        print(_("Umounting /sys..."))
                    error = subprocess.getoutput('umount   -lf \"' + os.path.join(self.customDir, "root/sys") + '\"')
                    if(error != ''):
                        print("error=\""+error+"\"")
                        self.suggestReboot('/sys could not be unmounted. It must be unmounted before you can build an ISO.')
                # umount /dev/pts
                if self.isMounted(os.path.join(self.customDir, "root/dev/pts")):
                    if silentMode == False:
                        print(_("Umounting /dev/pts..."))
                    error = subprocess.getoutput('umount  -lf \"' + os.path.join(self.customDir, "root/dev/pts") + '\"')
                    if(error != ''):
                        print("error=\""+error+"\"")
                        self.suggestReboot('/dev/pts could not be unmounted. It must be unmounted before you can build an ISO.')
                # umount /dev
                if self.isMounted(os.path.join(self.customDir, "root/dev")):
                    if silentMode == False:
                        print(_("Umounting /dev..."))
                    error = subprocess.getoutput('umount  -lf \"' + os.path.join(self.customDir, "root/dev") + '\"')
                    if(error != ''):
                        print("error=\""+error+"\"")
                        self.suggestReboot('/dev could not be unmounted. It must be unmounted before you can build an ISO.')
                # umount /run/dbus
                if self.isMounted(os.path.join(self.customDir, "root/run/dbus")):
                    if silentMode == False:
                        print(_("Umounting /run/dbus..."))
                    error = subprocess.getoutput('umount  -lf \"' + os.path.join(self.customDir, "root/run/dbus") + '\"')
                    if(error != ''):
                        print("error=\""+error+"\"")
                        self.suggestReboot('/run/dbus could not be unmounted. It must be unmounted before you can build an ISO.')
                if justUmount == False:
                    # restore wgetrc
                    if silentMode == False:
                        print(_("Restoring wgetrc configuration..."))
                    subprocess.getoutput('[ -f \"' +os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\" ] && ' + ' mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\"')
                    # remove apt.conf
                    #print(_("Removing apt.conf configuration..."))
                    #subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/apt/apt.conf") + '\"')
                    # remove dns info
                    # remove some locks
                    if silentMode == False:
                        print(_("Removing DNS info..."))
                    subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
                    subprocess.getoutput('ln -s /run/resolvconf/resolv.conf  ' + os.path.join(self.customDir, "root/etc/resolv.conf"))

                    #clean /run
                    if silentMode == False:
                        print(_("Clean /run ..."))
                    subprocess.getoutput('rm -rf  \"' + os.path.join(self.customDir, "root/run/*") + '\"')   
                # remove temp script
                subprocess.getoutput('rm -Rf /tmp/reconstructor-terminal.sh')
                self.TerminalInitialized = False

    def genericDialog(self,text):
        genericDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
        genericDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        genericDlg.set_icon_from_file(self.iconFile)
        genericDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        genericDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lblgenericInfo = Gtk.Label(text)
        genericDlg.vbox.pack_start(lblgenericInfo, expand=True, fill=True, padding=0)
        lblgenericInfo.show()
        genericDlg.run()
        genericDlg.destroy()

    def resolutionDialog(self,text, but1, but2, but3, but4, but5):
        BUT1 = 1
        BUT2 = 2
        BUT3 = 3
        BUT4 = 4
        BUT5 = 5
        resDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
        resDlg.add_buttons(but1, BUT1, but2, BUT2, but3, BUT3, but4, BUT4, but5, BUT5, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        resDlg.set_icon_from_file(self.iconFile)
        resDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        resDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lblresInfo = Gtk.Label(text)
        resDlg.vbox.pack_start(lblresInfo, expand=True, fill=True, padding=0)
        lblresInfo.show()
        response = resDlg.run()
        resDlg.destroy()

        if   response == BUT1:
            return but1
        elif response == BUT2:
            return but2
        elif response == BUT3:
            return but3
        elif response == BUT4:
            return but4
        elif response == BUT5:
            return but5
        else:
            return "cancel"

    def CheckForDesktopEnvironments(self):
        print('Detecting Desktop Environment...')
        butlist = list()
        cmdlist = list()

        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which startkde')
        if (deskenv != ""): print("KDE Found in Chroot Environment!"); butlist.append("KDE"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which /opt/kde3/bin/startkde')
        if (deskenv != ""): print("KDE3 Found in Chroot Environment!"); butlist.append("KDE3"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which xfce4-session')
        if (deskenv != ""): print("XFCE4 Found in Chroot Environment!"); butlist.append("XFCE4"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which gnome-session')
        if (deskenv != ""): print("GNOME Found in Chroot Environment!"); butlist.append("GNOME"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which startlxde')
        if (deskenv != ""): print("LXDE Found in Chroot Environment!"); butlist.append("LXDE"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which icewm-session')
        if (deskenv != ""): print("IceWM Found in Chroot Environment!"); butlist.append("IceWM"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which startfluxbox')
        if (deskenv != ""): print("Fluxbox Found in Chroot Environment!"); butlist.append("Fluxbox"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which wmaker')
        if (deskenv != ""): print("WindowMaker Found in Chroot Environment!"); butlist.append("WindowMaker"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which twm')
        if (deskenv != ""): print("TWM Found in Chroot Environment!"); butlist.append("TWM"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which /usr/share/e16/misc/starte16')
        if (deskenv != ""): print("Enlightenment (E16) Found in Chroot Environment!"); butlist.append("Enlightenment E16"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which /usr/share/e16/misc/starte16-kde')
        deskenv2 = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which startkde')
        if (deskenv != "" and deskenv2 != ""): print("Enlightenment (E16-KDE) Found in Chroot Environment!"); butlist.append("E16-KDE"); cmdlist.append(deskenv)
        deskenv = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which /usr/share/e16/misc/starte16-gnome')
        deskenv2 = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" which gnome-session')
        if (deskenv != "" and deskenv2 != ""): print("Enlightenment (E16-GNOME) Found in Chroot Environment!"); butlist.append("E16-GNOME"); cmdlist.append(deskenv)

        deskenvDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
        deskenvDlg.set_icon_from_file(self.iconFile)
        deskenvDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        deskenvDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lbldeskenvInfo = Gtk.Label("Choose Environment to customize.")
        deskenvDlg.vbox.pack_start(lbldeskenvInfo, expand=True, fill=True, padding=0)
        setsession = Gtk.CheckButton("Set as default session")
        deskenvDlg.vbox.pack_start(setsession, expand=True, fill=True, padding=0)
        setsession.show()

        lbldeskenvInfo.show()

        butlen = len(butlist)
        for i in range(0, butlen):
            deskenvDlg.add_button(butlist[i], i)

        response = deskenvDlg.run()

        if setsession.get_active() == True:
            print("Setting LiveCD Default Session...")
            # if the session alternative doesn't exist add it before setting it as the default session
            alternative = subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" update-alternatives --list x-session-manager | grep -i ' + cmdlist[response] )
            if (alternative != ""):
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" update-alternatives --set x-session-manager ' + cmdlist[response] )
            else:
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" update-alternatives --install /usr/bin/x-window-manager x-window-manager ' + cmdlist[response] +' 50' )
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" update-alternatives --set x-session-manager ' + cmdlist[response] )
            # confirm it was set properly
            print('Default Session set to: ' + subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" update-alternatives --list x-session-manager | grep -i ' + cmdlist[response] ) )

        deskenvDlg.destroy()
        return cmdlist[response]

    # Launches a chrooted xserver in Xephyr
    def launchChrootXephyr(self):
        try:
            if (subprocess.getoutput('which Xephyr') == ''):
                self.genericDialog("You must have Xephyr installed. Install Xephyr and try again." )
                return

            deskenv = self.CheckForDesktopEnvironments()
            print("Desktop Environment Selected: " + deskenv)

            scr = '#!/bin/sh\n#\n#\t(c) reconstructor, 2009\n#\n\n' + 'export DISPLAY=:2' + '\n' + deskenv + '\n'

            res = self.resolutionDialog("The ChrootXephyr feature is new and experimental.\n" \
                                        "It will allow you to graphically customize your environment.\n" \
                                        "When done, log out rather than just closing the window.\n" \
                                        "Please report any bugs you encounter.\n" \
                                        # TODO: Take out the above experimental notice next release or when we are sure it is stable.
                                        "\nChoose a Resolution.", "800x600","1024x768","1280x1024","1600x1200","1920x1200")
            if (res == 'cancel'):
                print('ChrootXephyr canceled by user:')
                return
            else :
                print('Resolution Selected: ' + res)

            f=open('/tmp/xephyr-chroot.sh', 'w')
            f.write(scr)
            f.close()
            subprocess.getoutput('chmod a+x ' + '/tmp/xephyr-chroot.sh')

            # setup environment
            # add current user to the access control list
            user = subprocess.getoutput('echo $USER')
            print(_("Adding user " + user + " to access control list..."))
            subprocess.getoutput('xhost +local:' + user)

            # make temp backup of /etc/skel files
            subprocess.getoutput('cp -f ' + os.path.join(self.customDir, "root/etc/skel/.bashrc") + ' ' + os.path.join(self.customDir, ".bashrc") )
            subprocess.getoutput('cp -f ' + os.path.join(self.customDir, "root/etc/skel/.bash_logout") + ' ' + os.path.join(self.customDir, ".bash_logout")  )
            subprocess.getoutput('cp -f ' + os.path.join(self.customDir, "root/etc/skel/.profile") + ' ' + os.path.join(self.customDir, ".profile") )

            # copy hosts
            subprocess.getoutput('cp -f /etc/hosts ' + os.path.join(self.customDir, "root/etc/hosts"))

            # copy Xauthority
            subprocess.getoutput('cp -f ~/.Xauthority ' + os.path.join(self.customDir, "root/root/.Xauthority"))

            #Fire up Xephyr on DISPLAY :2
            print('Launching Xephyr...')
            subprocess.getoutput('Xephyr -ac -screen ' + res + ' 2> /dev/null :2 &')  #+extension GLX, -extension GLX,
            subprocess.getoutput('export DISPLAY=:2')

            #Mount /tmp
            print(_("Mounting /tmp..."))
            subprocess.getoutput('mount --bind /tmp \"' + os.path.join(self.customDir, "root/tmp") + '\"')
            # copy dns info
            if os.path.exists("/etc/resolv.conf"):
                print(_("Copying DNS info..."))
                subprocess.getoutput('cp -L --remove-destination /etc/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            elif os.path.exists("/run/resolvconf/resolv.conf"):
                print(_("Copying DNS info..."))
                subprocess.getoutput('cp -L --remove-destination /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            #mount /run/dbus
            print(_("Mounting /run/dbus filesystem..."))
            if not os.path.exists(os.path.join(self.customDir, "root/run/dbus")):
                subprocess.getoutput("mkdir " + (os.path.join(self.customDir, "root/run/dbus")))
            subprocess.getoutput('mount --bind /run/dbus \"' + os.path.join(self.customDir, "root/run/dbus") + '\"')
            # mount /dev
            print(_("Mounting /dev filesystem..."))
            subprocess.getoutput('mount --bind /dev \"' + os.path.join(self.customDir, "root/dev") + '\"')
            # mount devpts
            print(_("Mounting devpts..."))
            subprocess.getoutput('mount -t devpts none \"' + os.path.join(self.customDir, "root/dev/pts") + '\"')
            # mount /proc
            print(_("Mounting /proc filesystem..."))
            subprocess.getoutput('mount -t proc none \"' + os.path.join(self.customDir, "root/proc") + '\"')
            # mount sysfs
            print(_("Mounting /sys filesystem..."))
            subprocess.getoutput('mount -t sysfs none \"' + os.path.join(self.customDir, "root/sys") + '\"')
            # copy apt.conf
            print(_("Copying apt configuration..."))
            if not os.path.exists(os.path.join(self.customDir, "root/etc/apt/apt.conf.d/")):
                os.makedirs(os.path.join(self.customDir, "root/etc/apt/apt.conf.d/"))
            subprocess.getoutput('cp -f /etc/apt/apt.conf.d/* ' + os.path.join(self.customDir, "root/etc/apt/apt.conf.d/"))
            # copy wgetrc
            print(_("Copying wgetrc configuration..."))
            # backup
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\"')
            subprocess.getoutput('cp -f /etc/wgetrc ' + os.path.join(self.customDir, "root/etc/wgetrc"))

            # create temporary script for chrooting
            subprocess.getoutput('export HOME="/root" ; chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/xephyr-chroot.sh')

            # restore wgetrc
            print(_("Restoring wgetrc configuration..."))
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\"')
            # remove apt.conf
            #print(_("Removing apt.conf configuration..."))
            #subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/apt/apt.conf") + '\"')
            # remove Xauthority
            subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/root/.Xauthority"))
            # remove hosts
            subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/etc/hosts"))

            # umount /tmp
            print(_("Umounting /tmp..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/tmp") + '\"')
            if(error != ''):
                self.suggestReboot('/tmp could not be unmounted. It must be unmounted before you can build an ISO.')
            # remove dns info
            print(_("Removing DNS info..."))
            subprocess.getoutput('rm -f \"' + os.path.join(self.customDir, "root/etc/resolv.conf") + '\"')
            subprocess.getoutput('ln -s /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            # umount /proc
            print(_("Umounting /proc..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/proc/") + '\"')
            if(error != ''):
                self.suggestReboot('/proc could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount /sys
            print(_("Umounting /sys..."))
            error = subprocess.getoutput('umount -fR \"' + os.path.join(self.customDir, "root/sys/") + '\"')
            if(error != ''):
                self.suggestReboot('/sys could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount devpts
            print(_("Umounting devpts..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/dev/pts") + '\"')
            if(error != ''):
                self.suggestReboot('/dev/pts could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount /dev
            print(_("Umounting /dev..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/dev/") + '\"')
            if(error != ''):
                self.suggestReboot('/dev could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount /run/dbus
            print(_("Umounting /run/dbus..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/run/dbus") + '\"')
            if(error != ''):
                self.suggestReboot('/run/dbus could not be unmounted. It must be unmounted before you can build an ISO.')
            # remove temp script
            subprocess.getoutput('rm -Rf /tmp/xephyr-chroot.sh')
            # startx complains about suspicious activity sometimes:P
            subprocess.getoutput('rm -Rf ' + os.path.join(self.customDir, "root/tmp/.X11-unix") )
            # return the display to :0
            subprocess.getoutput('export DISPLAY=:0')
            # copy /root to /etc/skel
            print(_("Customizing /etc/skel..."))
            subprocess.getoutput('rm -rf ' + os.path.join(self.customDir, "root/etc/skel"))
            subprocess.getoutput('cp -rf ' + os.path.join(self.customDir, "root/root") + ' ' + os.path.join(self.customDir, "root/etc/skel") )
            # Set proper permissions
            print(_("Setting /etc/skel permissions..."))
            subprocess.getoutput('chmod --recursive 755 ' + os.path.join(self.customDir, "root/etc/skel"))                        # All folders need to be drwxr-xr-x
            subprocess.getoutput('cd ' + os.path.join(self.customDir, "root/etc/skel") + '; ' + ' chmod 644 $(find . ! -type d)') # All files need to be -rw-r--r--
            # restore /etc/skel files
            subprocess.getoutput('mv -f ' + os.path.join(self.customDir, ".bashrc") + ' ' + os.path.join(self.customDir, "root/etc/skel/.bashrc"))
            subprocess.getoutput('mv -f ' + os.path.join(self.customDir, ".bash_logout") + ' ' + os.path.join(self.customDir, "root/etc/skel/.bash_logout"))
            subprocess.getoutput('mv -f ' + os.path.join(self.customDir, ".profile") + ' ' + os.path.join(self.customDir, "root/etc/skel/.profile"))
            # close the Xephyr window if it is still open
            subprocess.getoutput('pkill Xephyr')

        except Exception as detail:
            # restore settings
            # restore wgetrc
            print(_("Restoring wgetrc configuration..."))
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\"')
            # remove apt.conf
            #print(_("Removing apt.conf configuration..."))
            #subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/apt/apt.conf") + '\"')
            # remove dns info
            # remove Xauthority
            subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/root/.Xauthority"))
            # remove hosts
            subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/etc/hosts"))
            # umount /tmp
            print(_("Umounting /tmp..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/tmp") + '\"')
            if(error != ''):
                self.suggestReboot('/tmp could not be unmounted. It must be unmounted before you can build an ISO.')
            # remove dns info
            print(_("Removing DNS info..."))
            subprocess.getoutput('rm -f \"' + os.path.join(self.customDir, "root/etc/resolv.conf") + '\"')
            subprocess.getoutput('ln -s /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            # umount /proc
            print(_("Umounting /proc..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/proc/") + '\"')
            if(error != ''):
                self.suggestReboot('/proc could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount /sys
            print(_("Umounting /sys..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/sys/") + '\"')
            if(error != ''):
                self.suggestReboot('/sys could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount devpts
            print(_("Umounting devpts..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/dev/pts") + '\"')
            if(error != ''):
                self.suggestReboot('/dev/pts could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount /dev
            print(_("Umounting /dev..."))
            error = subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "root/dev/") + '\"')
            if(error != ''):
                self.suggestReboot('/dev could not be unmounted. It must be unmounted before you can build an ISO.')
            # remove temp script
            subprocess.getoutput('rm -Rf /tmp/xephyr-chroot.sh')
            # startx complains about suspicious activity sometimes:P
            subprocess.getoutput('rm -Rf ' + os.path.join(self.customDir, "root/tmp/.X11-unix") )
            # return the display to :0
            subprocess.getoutput('export DISPLAY=:0')
            # close the Xephyr window if it is still open
            subprocess.getoutput('pkill Xephyr')

            print(_("/etc/skel was not customized!"))
            errText = _('Error launching chrooted Xephyr: ')
            print(errText, detail)
            pass

        return

    # Sets live cd information (username, full name, hostname) for live cd
    def setLiveCdInfo(self, username, userFullname, userPassword, hostname):
        try:
            reUsername = None
            reFullname = None
            reHost = None
            conf = ''
            # dapper
            if self.cdUbuntuVersion == self.dapperVersion:
                # set live cd info
                f = open(os.path.join(self.customDir, "initrd/scripts/casper"), 'r')
                # regex for username
                reUsername = re.compile('USERNAME=\S+', re.IGNORECASE)
                # regex for user full name
                reFullname = re.compile('USERFULLNAME=\S+', re.IGNORECASE)
                # regex for hostname
                reHost = re.compile('HOST=\S+', re.IGNORECASE)
                # search
                for l in f:
                    if reUsername.search(l) != None:
                        if username != '':
                            #print(('Username: ' + l))
                            usernameText = _('Live CD Username: ')
                            print(usernameText + username)
                            l = 'USERNAME=\"' + username + '\"\n'
                    if reFullname.search(l) != None:
                        if userFullname != '':
                            #print(('User Full Name: ' + l))
                            userFullnameText = _('Live CD User Full name: ')
                            print(userFullnameText + userFullname)
                            l = 'USERFULLNAME=\"' + userFullname + '\"\n'
                    if reHost.search(l) != None:
                        if hostname != '':
                            #print(('Hostname: ' + l))
                            hostnameText = _('Live CD Hostname: ')
                            print(hostnameText + hostname)
                            l = 'HOST=\"' + hostname + '\"\n'

                    conf += l
            # edgy/feisty/gutsy
            elif self.cdUbuntuVersion == self.edgyVersion or self.cdUbuntuVersion == self.feistyVersion or self.cdUbuntuVersion == self.gutsyVersion or self.cdUbuntuVersion == self.hardyVersion or self.cdUbuntuVersion == self.intrepidVersion or self.cdUbuntuVersion == self.jauntyVersion  or self.cdUbuntuVersion == self.karmicVersion:
                # set live cd info
                f = open(os.path.join(self.customDir, "initrd/etc/casper.conf"), 'r')
                # regex for username
                reUsername = re.compile('export\sUSERNAME=\S+', re.IGNORECASE)
                # regex for user full name
                reFullname = re.compile('export\sUSERFULLNAME=\S+', re.IGNORECASE)
                # regex for hostname
                reHost = re.compile('export\sHOST=\S+', re.IGNORECASE)
                # search
                for l in f:
                    if reUsername.search(l) != None:
                        if username != '':
                            #print(('Username: ' + l))
                            usernameText = _('Live CD Username: ')
                            print(usernameText + username)
                            l = 'export USERNAME=\"' + username + '\"\n'
                    if reFullname.search(l) != None:
                        if userFullname != '':
                            #print(('User Full Name: ' + l))
                            userFullnameText = _('Live CD User Full name: ')
                            print(userFullnameText + userFullname)
                            l = 'export USERFULLNAME=\"' + userFullname + '\"\n'
                    if reHost.search(l) != None:
                        if hostname != '':
                            #print(('Hostname: ' + l))
                            hostnameText = _('Live CD Hostname: ')
                            print(hostnameText + hostname)
                            l = 'export HOST=\"' + hostname + '\"\n'

                    conf += l

                # close file
                f.close()

            # dapper
            if self.cdUbuntuVersion == self.dapperVersion:
                # re-write new file
                fc = open(os.path.join(self.customDir, "initrd/scripts/casper"), 'w')
                fc.write(conf)
                fc.close()
                # set execute bit for script
                subprocess.getoutput('chmod a+x \"' + os.path.join(self.customDir, "initrd/scripts/casper") + '\"')
            # edgy/feisty/gutsy
            elif self.cdUbuntuVersion == self.edgyVersion or self.cdUbuntuVersion == self.feistyVersion or self.cdUbuntuVersion == self.gutsyVersion or self.cdUbuntuVersion == self.hardyVersion or self.cdUbuntuVersion == self.intrepidVersion or self.cdUbuntuVersion == self.jauntyVersion  or self.cdUbuntuVersion == self.karmicVersion:
                # re-write new file
                fc = open(os.path.join(self.customDir, "initrd/etc/casper.conf"), 'w')
                fc.write(conf)
                fc.close()
                # set execute bit for script
                subprocess.getoutput('chmod a+x \"' + os.path.join(self.customDir, "initrd/etc/casper.conf") + '\"')
            # unknown
            else:
                return

            # set password
            adduser_script=subprocess.getoutput('find ' + os.path.join(self.customDir, "initrd") + ' -name \"[[:digit:]]*adduser\" | head -n 1')
            
            if adduser_script != "":
                fp = open(adduser_script, 'r')
                # regex for username
                rePassword = re.compile('set passwd/user-password-crypted\s\w+', re.IGNORECASE)
                conf = ''
                # search
                for l in fp:
                    if rePassword.search(l) != None:
                        if userPassword != '':
                            #print(('Password: ' + l))
                            passwordText = _('Setting Live CD Password... ')
                            print(passwordText)
                            #print("DEBUG: Password: " + userPassword + " des Hash: " + subprocess.getoutput('echo ' + userPassword + ' | mkpasswd -s -H des'))
                            l = 'set passwd/user-password-crypted ' + subprocess.getoutput('echo ' + userPassword + ' | mkpasswd -s -H des') + '\n'

                    conf += l
                # close file
                fp.close()

                # re-write new file
                fpc = open(adduser_script, 'w')
                fpc.write(conf)
                fpc.close()
                # set execute bit for script
                subprocess.getoutput('chmod a+x \"' + adduser_script + '\"')

        except Exception as detail:
            errText = _('Error setting user info: ')
            print(errText, detail)
            pass

    # Burns ISO
    def burnIso(self):
        try:
            if subprocess.getoutput('which nautilus-cd-burner') != '':
                print(_('Burning ISO...'))
                subprocess.getoutput('nautilus-cd-burner --source-iso=\"' + self.buildLiveCdFilename + '\"')
            else:
                print(_('Error: nautilus-cd-burner is needed for burning iso files... '))

        except Exception as detail:
            errText = _('Error burning ISO: ')
            print(errText, detail)
            pass

    def burnAltIso(self):
        try:
            if subprocess.getoutput('which nautilus-cd-burner') != '':
                print(_('Burning ISO...'))
                subprocess.getoutput('nautilus-cd-burner --source-iso=\"' + self.buildAltCdFilename + '\"')
            else:
                print(_('Error: nautilus-cd-burner is needed for burning iso files... '))

        except Exception as detail:
            errText = _('Error burning ISO: ')
            print(errText, detail)
            pass

    def loadBootMenuColor(self):
        try:
            print(_("Loading Boot Menu Color..."))
            if os.path.exists(os.path.join(self.customDir, "remaster/isolinux/isolinux.cfg")):
                #color = self.builder.get_object("colorbuttonBrowseLiveCdTextColor").get_color()
                #rgbColor = color.red/255, color.green/255, color.blue/255
                #hexColor = '%02x%02x%02x' % rgbColor
                # find text color config line in isolinux.cfg
                f = open(os.path.join(self.customDir, "remaster/isolinux/isolinux.cfg"), 'r')
                color = ''
                line = ''
                # config line regex
                r = re.compile('GFXBOOT-BACKGROUND*', re.IGNORECASE)
                # find config string
                for l in f:
                    if r.search(l) != None:
                        line = l

                f.close()
                # color regex
                r = re.compile('\w+-\w+\s\d\w(\w+)', re.IGNORECASE)
                m = r.match(line)
                if m != None:
                    color = m.group(1)
                    print(_('Live CD Text Color: ') + color)
                    # set colorbutton to color
                    self.builder.get_object("colorbuttonBrowseLiveCdTextColor").set_color(Gdk.color_parse('#' + color))
        except Exception as detail:
            errText = _("Error getting boot menu color: ")
            print(errText, detail)
            pass

    def loadGdmBackgroundColor(self):
        try:
            print(_("Loading GDM Background Color..."))
            if os.path.exists(os.path.join(self.customDir, "root/etc/gdm/gdm.conf-custom")):
                # find text color config line in gdm.conf-custom
                f = open(os.path.join(self.customDir, "root/etc/gdm/gdm.conf-custom"), 'r')
                color = ''
                line = ''
                # config line regex
                r = re.compile('GraphicalThemedColor*', re.IGNORECASE)
                # find config string
                for l in f:
                    if r.search(l) != None:
                        line = l

                f.close()
                if line == '':
                    print(_('GDM background color not found in gdm.conf-custom. Using gdm.conf...'))
                    # get from gdm.conf
                    # find text color config line in gdm.conf
                    f = open(os.path.join(self.customDir, "root/etc/gdm/gdm.conf"), 'r')
                    color = ''
                    line = ''
                    # config line regex
                    r = re.compile('GraphicalThemedColor*', re.IGNORECASE)
                    # find config string
                    for l in f:
                        if r.search(l) != None:
                            line = l

                    f.close()
                # color regex
                r = re.compile('\w+=#(\w+)', re.IGNORECASE)
                m = r.match(line)
                if m != None:
                    color = m.group(1)
                    print(_('GDM Background Color: ') + color)
                    # set var & colorbutton to color
                    self.gdmBackgroundColor = color
                    self.builder.get_object("colorbuttonBrowseGdmBackgroundColor").set_color(Gdk.color_parse('#' + color))

        except Exception as detail:
            errText = _("Error getting GDM background color: ")
            print(errText, detail)
            pass

    # startup optimization
    def optimizeStartup(self):
        try:
            print(_('Optimizing Startup...'))
            # HACK: create temp script to set links...
            scr = '#!/bin/sh\n#\n# startup-optimize.sh\n#\t(c) reconstructor team, 2006\n\n'
            # get startup daemons and set accordingly
            # ppp
            if self.builder.get_object("checkbuttonStartupPpp").get_active() == True:
                print(_('Enabling Startup Daemon: ppp'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/ppp S14ppp 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/ppp S14ppp 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/ppp S14ppp 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/ppp S14ppp 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: ppp'))
                scr += 'rm /etc/rc2.d/S14ppp 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S14ppp 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S14ppp 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S14ppp 1>&2 2>/dev/null\n'
            # hplip
            if self.builder.get_object("checkbuttonStartupHplip").get_active() == True:
                print(_('Enabling Startup Daemon: hplip'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/hplip S18hplip 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/hplip S18hplip 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/hplip S18hplip 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/hplip S18hplip 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: hplip'))
                scr += 'rm /etc/rc2.d/S18hplip 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S18hplip 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S18hplip 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S18hplip 1>&2 2>/dev/null\n'
            # cupsys
            if self.builder.get_object("checkbuttonStartupCupsys").get_active() == True:
                print(_('Enabling Startup Daemon: cupsys'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/cupsys S19cupsys 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/cupsys S19cupsys 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/cupsys S19cupsys 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/cupsys S19cupsys 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: cupsys'))
                scr += 'rm /etc/rc2.d/S19cupsys 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S19cupsys 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S19cupsys 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S19cupsys 1>&2 2>/dev/null\n'
            # festival
            if self.builder.get_object("checkbuttonStartupFestival").get_active() == True:
                print(_('Enabling Startup Daemon: festival'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/festival S20festival 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/festival S20festival 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/festival S20festival 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/festival S20festival 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: festival'))
                scr += 'rm /etc/rc2.d/S20festival 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S20festival 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S20festival 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S20festival 1>&2 2>/dev/null\n'
            # laptop-mode
            if self.builder.get_object("checkbuttonStartupLaptopMode").get_active() == True:
                print(_('Enabling Startup Daemon: laptop-mode'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/laptop-mode S20laptop-mode 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/laptop-mode S20laptop-mode 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/laptop-mode S20laptop-mode 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/laptop-mode S20laptop-mode 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: laptop-mode'))
                scr += 'rm /etc/rc2.d/S20laptop-mode 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S20laptop-mode 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S20laptop-mode 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S20laptop-mode 1>&2 2>/dev/null\n'
            # nvidia-kernel
            if self.builder.get_object("checkbuttonStartupNvidiaKernel").get_active() == True:
                print(_('Enabling Startup Daemon: nvidia-kernel'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/nvidia-kernel S20nvidia-kernel 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/nvidia-kernel S20nvidia-kernel 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/nvidia-kernel S20nvidia-kernel 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/nvidia-kernel S20nvidia-kernel 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: nvidia-kernel'))
                scr += 'rm /etc/rc2.d/S20nvidia-kernel 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S20nvidia-kernel 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S20nvidia-kernel 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S20nvidia-kernel 1>&2 2>/dev/null\n'
            # rsync
            if self.builder.get_object("checkbuttonStartupRsync").get_active() == True:
                print(_('Enabling Startup Daemon: rsync'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/rsync S20rsync 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/rsync S20rsync 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/rsync S20rsync 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/rsync S20rsync 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: rsync'))
                scr += 'rm /etc/rc2.d/S20rsync 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S20rsync 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S20rsync 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S20rsync 1>&2 2>/dev/null\n'
            # bluez-utils
            if self.builder.get_object("checkbuttonStartupBluezUtils").get_active() == True:
                print(_('Enabling Startup Daemon: bluez-utils'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/bluez-utils S25bluez-utils 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/bluez-utils S25bluez-utils 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/bluez-utils S25bluez-utils 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/bluez-utils S25bluez-utils 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: bluez-utils'))
                scr += 'rm /etc/rc2.d/S25bluez-utils 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S25bluez-utils 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S25bluez-utils 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S25bluez-utils 1>&2 2>/dev/null\n'
            # mdadm
            if self.builder.get_object("checkbuttonStartupMdadm").get_active() == True:
                print(_('Enabling Startup Daemon: mdadm'))
                scr += 'cd /etc/rc2.d ; ln -s ../init.d/mdadm S25mdadm 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc3.d ; ln -s ../init.d/mdadm S25mdadm 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc4.d ; ln -s ../init.d/mdadm S25mdadm 1>&2 2>/dev/null\n'
                scr += 'cd /etc/rc5.d ; ln -s ../init.d/mdadm S25mdadm 1>&2 2>/dev/null\n'
            else:
                print(_('Disabling Startup Daemon: mdadm'))
                scr += 'rm /etc/rc2.d/S25mdadm 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc3.d/S25mdadm 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc4.d/S25mdadm 1>&2 2>/dev/null\n'
                scr += 'rm /etc/rc5.d/S25mdadm 1>&2 2>/dev/null\n'



            f=open(os.path.join(self.customDir, "root/tmp/startup-optimize.sh"), 'w')
            f.write(scr)
            f.close()
            subprocess.getoutput('chmod a+x \"' + os.path.join(self.customDir, "root/tmp/startup-optimize.sh") + '\"')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/startup-optimize.sh')
            # cleanup
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/tmp/startup-optimize.sh") + '\"')

        except Exception as detail:
            self.setDefaultCursor()
            errText = _('Error setting startup daemons: ')
            print(errText, detail)
            pass

    # shutdown optimization
    def optimizeShutdown(self):
        try:
            print(_('Optimizing shutdown scripts...'))
            for s in self.shutdownScripts:
                # rename script to make inactive
                subprocess.getoutput('mv ' + os.path.join(self.customDir, "root/etc/rc0.d/") + 'K' + s + ' ' + os.path.join(self.customDir, "root/etc/rc0.d/") + '_' + s + ' 1>&2 2>/dev/null')
        except Exception as detail:
            errText = _('Error optimizing shutdown scripts: ')
            print(errText, detail)
            pass

    # restore original shutdown
    def restoreShutdown(self):
        try:
            print(_('Restoring original shutdown scripts...'))
            for s in self.shutdownScripts:
                # rename script to make active
                subprocess.getoutput('mv ' + os.path.join(self.customDir, "root/etc/rc0.d/") + '_' + s + ' ' + os.path.join(self.customDir, "root/etc/rc0.d/") + 'K' + s + ' 1>&2 2>/dev/null')
            # unselect optimization
            self.builder.get_object("checkbuttonOptimizationShutdown").set_active(False)
            self.setDefaultCursor()
        except Exception as detail:
            self.setDefaultCursor()
            errText = _('Error restoring original shutdown scripts: ')
            print(errText, detail)
            pass

    def loadGdmThemes(self):
        try:
            print(_("Loading GDM Themes..."))
            themesDir = None
            if os.path.exists(os.path.join(self.customDir, "root/usr/share/gdm/themes/")):
                themesDir = os.path.join(self.customDir, "root/usr/share/gdm/themes/")
            themes = []
            # find themes
            if themesDir != None:
                for themeItem in os.listdir(themesDir):
                    # if dir, check
                    themeItemDir = os.path.join(themesDir, themeItem)
                    if os.path.isdir(themeItemDir):
                        # check for theme
                        if os.path.exists(os.path.join(themeItemDir, "GdmGreeterTheme.desktop")):
                            # is theme, add to list
                            themes.append(themeItem)

            # add items to combobox
            themeList = Gtk.ListStore(GObject.TYPE_STRING)
            for theme in themes:
                themeList.append([theme])

            self.builder.get_object("comboboxentryGnomeGdmTheme").set_model(themeList)
            self.builder.get_object("comboboxentryGnomeGdmTheme").set_entry_text_column(0)
        except Exception as detail:
            errText = _("Error loading GDM Themes: ")
            print(errText, detail)
            pass
    def loadGnomeThemes(self):
        try:
            print(_("Loading Gnome Themes and Icons..."))
            themesDir = None
            iconsDir = None
            if os.path.exists(os.path.join(self.customDir, "root/usr/share/themes/")):
                themesDir = os.path.join(self.customDir, "root/usr/share/themes/")
            if os.path.exists(os.path.join(self.customDir, "root/usr/share/icons/")):
                iconsDir = os.path.join(self.customDir, "root/usr/share/icons/")
            themes = []
            borders = []
            icons = []
            # find themes
            if themesDir != None:
                for themeItem in os.listdir(themesDir):
                    # if dir, check
                    themeItemDir = os.path.join(themesDir, themeItem)
                    if os.path.isdir(themeItemDir):
                        # check for theme
                        if os.path.exists(os.path.join(themeItemDir, "gtk-2.0/")):
                            # is theme, add to list
                            themes.append(themeItem)
                        # check for controls
                        if os.path.exists(os.path.join(themeItemDir, "metacity-1/")):
                            borders.append(themeItem)

            # find icons
            if iconsDir != None:
                for iconItem in os.listdir(iconsDir):
                    # if dir, check for icons
                    iconItemDir = os.path.join(iconsDir, iconItem)
                    if os.path.isdir(iconItemDir):
                        # check for icon index
                        if os.path.exists(os.path.join(iconItemDir, "index.theme")):
                            # index exists, add to list
                            icons.append(iconItem)

            # add items to comboboxes
            themeList = Gtk.ListStore(GObject.TYPE_STRING)
            borderList = Gtk.ListStore(GObject.TYPE_STRING)
            iconList = Gtk.ListStore(GObject.TYPE_STRING)
            for theme in themes:
                themeList.append([theme])
            for border in borders:
                borderList.append([border])
            for icon in icons:
                iconList.append([icon])

            self.builder.get_object("comboboxentryGnomeTheme").set_model(themeList)
            self.builder.get_object("comboboxentryGnomeTheme").set_entry_text_column(0)
            self.builder.get_object("comboboxentryGnomeThemeWindowBorders").set_model(borderList)
            self.builder.get_object("comboboxentryGnomeThemeWindowBorders").set_entry_text_column(0)
            self.builder.get_object("comboboxentryGnomeThemeIcons").set_model(iconList)
            self.builder.get_object("comboboxentryGnomeThemeIcons").set_entry_text_column(0)
        except Exception as detail:
            errText = _("Error loading Gnome themes: ")
            print(errText, detail)
            pass

    def FileSize(self,path):
        size = 0
        for root , dirs, files in os.walk(path, True):
            for name in files:
                if os.path.exists(os.path.join(root, name)) :
                    if not os.path.islink(os.path.join(root, name)):
                        size += int(round((os.path.getsize(os.path.join(root, name))+4093)/4096)*4)
        return size

    def calculateIsoSize(self):
        try:
            self.setBusyCursor()
            self.doneTerminal(forceMode=True,silentMode=True,justUmount=False)

            # reset current size
            self.builder.get_object("labelSoftwareIsoSize").set_text("")
            totalSize = None
            remasterSize = 0
            rootSize = 0
            squashSize = 0
            print(_('Calculating Live ISO Size...'))
            self.showProgress(_('Calculating Live ISO Size...'),0.20)
            yield True

            self.setBusyCursor()
            remasterSize = self.FileSize(os.path.join(self.customDir,"remaster/"))
            # subtract squashfs root
            if os.path.exists(os.path.join(self.customDir, "remaster/casper/filesystem.squashfs")):
                squashSize = int(round(os.path.getsize(os.path.join(self.customDir, "remaster/casper/filesystem.squashfs"))/1024))

            remasterSize -= squashSize
            # get size of root dir
            rootSize = self.FileSize(os.path.join(self.customDir, "root/"))
            # divide root size to simulate squash compression
            SoftwareIsoSize = int(round((remasterSize + (rootSize/3.55))/1024))
            self.builder.get_object("labelSoftwareIsoSize").set_text( '~ ' + str(SoftwareIsoSize) + ' MB')
            self.showProgress(_("Finished Calculating Live ISO Size."),0.25)
            #self.setDefaultCursor()
            # set page here - since this is run on a background thread,
            # the next page will show too quickly if set in self.checkPage()
            self.setPage(self.pageLiveCustomize)
        except Exception as detail:
            errText = _("Error calculating estimated iso size: ")
            print(errText, detail)
            pass
        self.setDefaultCursor()
        yield False

    def calculateAltIsoSize(self):
        try:
            # reset current size
            self.builder.get_object("labelAltIsoSize").set_text("")
            totalSize = None
            remasterSize = 0
            print(_('Calculating Alternate ISO Size...'))
            self.showProgress(_('Calculating Alternate ISO Size...'))
            yield True
            self.setBusyCursor()
            remasterSize = self.FileSize(os.path.join(self.customDir, self.altRemasterDir))

            self.builder.get_object("labelAltIsoSize").set_text( '~ ' + str(int(round(remasterSize/1024))) + ' MB')
            self.setDefaultCursor()
            self.showProgress(_("Finished Calculating Altername ISO Size."),0.35)
            # set page here - since this is run on a background thread,
            # the next page will show too quickly if set in self.checkPage()
            self.setPage(self.pageAltCustomize)
        except Exception as detail:
            errText = _("Error calculating estimated iso size: ")
            print(errText, detail)
            pass
        self.setDefaultCursor()
        yield False

    def startInteractiveEdit(self):
        print(_('Beginning Interactive Editing...'))
        # set interactive edit tag
        self.interactiveEdit = True
        # check for template user home directory; create if necessary
        #print(('useradd -d /home/reconstructor -m -s /bin/bash -p ' + str(os.urandom(8))))
        if os.path.exists('/home/reconstructor') == False:
            # create user with random password
            password = 'r0714'
            subprocess.getoutput('useradd -d /home/reconstructor -s /bin/bash -p ' + password +' reconstructor')
            # create home dir
            subprocess.getoutput('mkdir -p /home/reconstructor')
            # change owner of home
            subprocess.getoutput('chown -R reconstructor /home/reconstructor')
        # launch Xnest in background
        try:
            print(_('Starting Xnest in the background...'))
            subprocess.getoutput('Xnest :1 -ac -once & 1>&2 2>/dev/null')
        except Exception as detail:
            errXnest = _("Error starting Xnest: ")
            print(errXnest, detail)
            return
        # try to start gnome-session with template user
        try:
            print(_('Starting Gnome-Session....'))
            #subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\" ' + 'su -c \"export DISPLAY=localhost:1 ; gnome-session\" 1>&2 2>/dev/null\"')
            #subprocess.getoutput("chroot /home/ehazlett/reconstructor/root \"/tmp/test.sh\"")
            subprocess.getoutput('su reconstructor -c \"export DISPLAY=:1 ; gnome-session\" 1>&2 2>/dev/null')
        except Exception as detail:
            errGnome = _("Error starting Gnome-Session: ")
            print(errGnome, detail)
            return

    def clearInteractiveSettings(self):
        try:
            print(_('Clearing Interactive Settings...'))
            print(_('Removing \'reconstructor\' user...'))
            subprocess.getoutput('userdel reconstructor')
            print(_('Removing \'reconstructor\' home directory...'))
            subprocess.getoutput('rm -Rf /home/reconstructor')
            self.setDefaultCursor()
        except Exception as detail:
            self.setDefaultCursor()
            errText = _('Error clearing interactive settings: ')
            print(errText, detail)
            pass

    def getGpgKeyInfo(self):
        # show dialog for key info
        keyDlg = Gtk.Dialog(title="Installation Key", parent=None)
        keyDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        keyDlg.set_icon_from_file('glade/app.png')
        keyDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        keyDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        infoText = _("<b>GPG Installation Key Information</b>")
        lblInfo = Gtk.Label(infoText)
        lblInfo.set_use_markup(True)
        # email entry
        hboxEmail = Gtk.HBox()
        emailText = _("Email:")
        labelEmail = Gtk.Label(emailText)
        hboxEmail.pack_start(labelEmail, expand=False, fill=False, padding=5)
        entryEmail = Gtk.Entry()
        hboxEmail.pack_start(entryEmail, expand=True, fill=True, padding=0)
        # password entry
        hboxPassword = Gtk.HBox()
        passText = _("Password:")
        labelPassword = Gtk.Label(passText)
        hboxPassword.pack_start(labelPassword, expand=False, fill=False, padding=5)
        entryPassword = Gtk.Entry()
        entryPassword.set_visibility(False)
        hboxPassword.pack_start(entryPassword, expand=True, fill=True, padding=0)
        # password confirm entry
        hboxPasswordConfirm = Gtk.HBox()
        passConfirmText = _("Confirm:")
        labelPasswordConfirm = Gtk.Label(passConfirmText)
        hboxPasswordConfirm.pack_start(labelPasswordConfirm, expand=False, fill=False, padding=11)
        entryPasswordConfirm = Gtk.Entry()
        entryPasswordConfirm.set_visibility(False)
        hboxPasswordConfirm.pack_start(entryPasswordConfirm, expand=True, fill=True, padding=0)

        keyDlg.vbox.pack_start(lblInfo, expand=False, fill=False, padding=0)
        #keyDlg.vbox.pack_start(labelEmail, expand=True, fill=True, padding=0)
        #keyDlg.vbox.pack_start(entryEmail, expand=True, fill=True, padding=0)
        keyDlg.vbox.pack_start(hboxEmail, expand=True, fill=True, padding=0)
        keyDlg.vbox.pack_start(hboxPassword, expand=True, fill=True, padding=0)
        keyDlg.vbox.pack_start(hboxPasswordConfirm, expand=True, fill=True, padding=0)
        #keyDlg.vbox.pack_start(labelPassword, expand=True, fill=True, padding=0)
        #keyDlg.vbox.pack_start(entryPassword, expand=True, fill=True, padding=0)
        #keyDlg.vbox.pack_start(entryPasswordConfirm, expand=True, fill=True, padding=0)
        lblInfo.show()
        labelEmail.show()
        entryEmail.show()
        hboxEmail.show()
        labelPassword.show()
        entryPassword.show()
        labelPasswordConfirm.show()
        entryPasswordConfirm.show()
        hboxPassword.show()
        hboxPasswordConfirm.show()
        response = keyDlg.run()
        info = None
        if response == Gtk.ResponseType.OK :
            if entryPassword.get_text() == entryPasswordConfirm.get_text():
                info = (entryEmail.get_text(), entryPasswordConfirm.get_text())
            else:
                print(_("Passwords do not match..."))
        else:
            print(_("GPG generation cancelled..."))

        keyDlg.destroy()
        return info

    def on_buttonBack_clicked(self, widget):
        # HACK: back pressed so change buttonNext text
        self.builder.get_object("buttonNext").set_label("Next")
        # HACK: get_current_page() returns after the click, so check for 1 page ahead
        # check for first step; disable if needed
        if self.builder.get_object("notebookWizard").get_current_page() == 1:
            self.builder.get_object("buttonBack").hide()
        # check for disc type and move to proper locations
        if self.builder.get_object("notebookWizard").get_current_page() == self.pageAltSetup:
            self.setPage(self.pageDiscType)
        elif self.builder.get_object("notebookWizard").get_current_page() == self.pageFinish:
            # on finish page; move to proper disc type build
            if self.discType == "live":
                self.setPage(self.pageLiveBuild)
            elif self.discType == "alt":
                self.setPage(self.pageAltBuild)
        else:
            self.builder.get_object("notebookWizard").prev_page()

    def on_buttonNext_clicked(self, widget):
        page = self.builder.get_object("notebookWizard").get_current_page()
        # HACK: show back button
        self.builder.get_object("buttonBack").show()
        #if (self.checkPage(page)):
        #    self.builder.get_object("notebookWizard").next_page()
        self.checkPage(page)

    def on_buttonBrowseWorkingDir_clicked(self, widget):
        dlgTitle = _('Select Working Directory')
        workingDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.SELECT_FOLDER)
        workingDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        workingDlg.set_uri(os.environ['HOME'] + '/reconstructor')
        response = workingDlg.run()
        if response == Gtk.ResponseType.OK :
            filename = workingDlg.get_current_folder()
            self.builder.get_object("entryWorkingDir").set_text(workingDlg.get_filename())
            self.customDir = workingDlg.get_filename()
            self.readConfig()
            workingDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            workingDlg.destroy()

    def on_buttonBrowseIsoFilename_clicked(self, widget):
        # filter only iso files
        isoFilter = Gtk.FileFilter()
        isoFilter.set_name("ISO Files (.iso)")
        isoFilter.add_pattern("*.iso")
        # create dialog
        dlgTitle = _('Select Live CD ISO')
        isoDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        isoDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        isoDlg.add_filter(isoFilter)
        isoDlg.set_current_folder(os.environ['HOME'])
        response = isoDlg.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("entryIsoFilename").set_text(isoDlg.get_filename())
            isoDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            isoDlg.destroy()

    def on_buttonBrowseLiveCdFilename_clicked(self, widget):
        # filter only iso files
        isoFilter = Gtk.FileFilter()
        isoFilter.set_name("ISO Files")
        isoFilter.add_pattern("*.iso")
        # create dialog
        dlgTitle = _('Select Live CD Filename')
        isoDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.SAVE)
        isoDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        isoDlg.add_filter(isoFilter)
        isoDlg.set_select_multiple(False)
        isoDlg.set_current_folder(os.environ['HOME'])
        response = isoDlg.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("entryLiveIsoFilename").set_text(isoDlg.get_filename())
            isoDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            isoDlg.destroy()

    def on_buttonBrowseAltCdFilename_clicked(self, widget):
        # filter only iso files
        isoFilter = Gtk.FileFilter()
        isoFilter.set_name("ISO Files")
        isoFilter.add_pattern("*.iso")
        # create dialog
        dlgTitle = _('Select Alternate CD Filename')
        isoDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.SAVE)
        isoDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        isoDlg.add_filter(isoFilter)
        isoDlg.set_select_multiple(False)
        isoDlg.set_current_folder(os.environ['HOME'])
        response = isoDlg.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("entryAltBuildIsoFilename").set_text(isoDlg.get_filename())
            isoDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            isoDlg.destroy()

    def on_checkbuttonBuildIso_toggled(self, widget):
        if self.builder.get_object("checkbuttonBuildIso").get_active() == True:
            # show filename, description, etc. entry
            self.builder.get_object("tableLiveCd").show()
        else:
            # hide filename entry
            self.builder.get_object("tableLiveCd").hide()

    def on_checkbuttonAltBuildIso_toggled(self, widget):
        if self.builder.get_object("checkbuttonAltBuildIso").get_active() == True:
            # show filename, description, etc. entry
            self.builder.get_object("tableAltCd").show()
        else:
            # hide filename entry
            self.builder.get_object("tableAltCd").hide()


    def on_buttonBrowseGnomeDesktopWallpaper_clicked(self, widget):
        # filter only image files
        imgFilter = Gtk.FileFilter()
        imgFilter.set_name("Images (.jpg, .png, .bmp)")
        imgFilter.add_pattern("*jpeg")
        imgFilter.add_pattern("*.jpg")
        imgFilter.add_pattern("*.png")
        imgFilter.add_pattern("*.bmp")
        # create dialog
        dlgTitle = _('Select Wallpaper')
        imgDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        imgDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        imgDlg.add_filter(imgFilter)
        imgDlg.set_select_multiple(False)
        response = imgDlg.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("entryGnomeDesktopWallpaperFilename").set_text(imgDlg.get_filename())
            imgDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            imgDlg.destroy()


    def on_buttonBrowseGnomeFont_clicked(self, widget):
        # font selection dialog
        fontDialog = Gtk.FontSelectionDialog(title="Select Font")
        response = fontDialog.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("labelGnomeDesktopApplicationFontValue").set_text(fontDialog.get_font_name())
            fontDialog.destroy()
        else:
            fontDialog.destroy()

    def on_buttonBrowseGnomeDocumentFont_clicked(self, widget):
        # font selection dialog
        dlgTitle = _('Select Font')
        fontDialog = Gtk.FontSelectionDialog(title=dlgTitle)
        response = fontDialog.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("labelGnomeDesktopDocumentFontValue").set_text(fontDialog.get_font_name())
            fontDialog.destroy()
        else:
            fontDialog.destroy()

    def on_buttonBrowseGnomeDesktopFont_clicked(self, widget):
        # font selection dialog
        dlgTitle = _('Select Font')
        fontDialog = Gtk.FontSelectionDialog(title=dlgTitle)
        response = fontDialog.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("labelGnomeDesktopFontValue").set_text(fontDialog.get_font_name())
            fontDialog.destroy()
        else:
            fontDialog.destroy()

    def on_buttonBrowseGnomeDesktopTitleBarFont_clicked(self, widget):
        # font selection dialog
        dlgTitle = _('Select Font')
        fontDialog = Gtk.FontSelectionDialog(title=dlgTitle)
        response = fontDialog.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("labelGnomeDesktopTitleBarFontValue").set_text(fontDialog.get_font_name())
            fontDialog.destroy()
        else:
            fontDialog.destroy()

    def on_buttonBrowseGnomeFixedFont_clicked(self, widget):
        # font selection dialog
        dlgTitle = _('Select Font')
        fontDialog = Gtk.FontSelectionDialog(title=dlgTitle)
        response = fontDialog.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("labelGnomeDesktopFixedFontValue").set_text(fontDialog.get_font_name())
            fontDialog.destroy()
        else:
            fontDialog.destroy()

    def on_buttonImportGnomeTheme_clicked(self, widget):
        print(_("Importing Theme..."))
        # filter only tar.gz files
        dlgFilter = Gtk.FileFilter()
        dlgFilter.set_name("Archives (.tar.gz, .tar.bz2)")
        dlgFilter.add_pattern("*tar.gz")
        dlgFilter.add_pattern("*tar.bz2")
        # create dialog
        dlgTitle = _('Select Theme Package')
        dlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dlg.add_filter(dlgFilter)
        dlg.set_select_multiple(False)
        response = dlg.run()
        if response == Gtk.ResponseType.OK :
            # extract theme into root
            # check for bzip or gzip
            fname, ext = os.path.splitext(dlg.get_filename())
            if ext == ".gz":
                # gzip
                subprocess.getoutput('tar zxf \"' + dlg.get_filename() + '\" -C \"' + os.path.join(self.customDir, "root/usr/share/themes/") + '\"')
            elif ext == ".bz2":
                # bzip
                subprocess.getoutput('tar jxf \"' + dlg.get_filename() + '\" -C \"' + os.path.join(self.customDir, "root/usr/share/themes/") + '\"')

            # reload gnome themes
            self.loadGnomeThemes()
            dlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            print(_("Import Cancelled..."))
            dlg.destroy()

    def on_buttonImportGnomeThemeIcons_clicked(self, widget):
        print(_("Importing Icons..."))
        # filter only tar.gz files
        dlgFilter = Gtk.FileFilter()
        dlgFilter.set_name("Archives (.tar.gz, .tar.bz2)")
        dlgFilter.add_pattern("*tar.gz")
        dlgFilter.add_pattern("*tar.bz2")
        # create dialog
        dlgTitle = _('Select Icon Package')
        dlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dlg.add_filter(dlgFilter)
        dlg.set_select_multiple(False)
        response = dlg.run()
        if response == Gtk.ResponseType.OK :
            # extract theme into root
            # check for bzip or gzip
            fname, ext = os.path.splitext(dlg.get_filename())
            if ext == ".gz":
                # gzip
                subprocess.getoutput('tar zxf \"' + dlg.get_filename() + '\" -C \"' + os.path.join(self.customDir, "root/usr/share/icons/") + '\"')
            elif ext == ".bz2":
                # bzip
                subprocess.getoutput('tar jxf \"' + dlg.get_filename() + '\" -C \"' + os.path.join(self.customDir, "root/usr/share/icons/") + '\"')

            # reload gnome themes
            self.loadGnomeThemes()
            dlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            print(_("Import Cancelled..."))
            dlg.destroy()

    def on_buttonImportGdmTheme_clicked(self, widget):
        print(_("Importing GDM Theme..."))
        # filter only tar.gz files
        dlgFilter = Gtk.FileFilter()
        dlgFilter.set_name("Archives (.tar.gz, .tar.bz2)")
        dlgFilter.add_pattern("*tar.gz")
        dlgFilter.add_pattern("*tar.bz2")
        # create dialog
        dlgTitle = _('Select GDM Theme Package')
        dlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dlg.add_filter(dlgFilter)
        dlg.set_select_multiple(False)
        response = dlg.run()
        if response == Gtk.ResponseType.OK :
            # extract theme into root
            # check for bzip or gzip
            fname, ext = os.path.splitext(dlg.get_filename())
            if ext == ".gz":
                # gzip
                subprocess.getoutput('tar zxf \"' + dlg.get_filename() + '\" -C \"' + os.path.join(self.customDir, "root/usr/share/gdm/themes/") + '\"')
            elif ext == ".bz2":
                # bzip
                subprocess.getoutput('tar jxf \"' + dlg.get_filename() + '\" -C \"' + os.path.join(self.customDir, "root/usr/share/gdm/themes/") + '\"')
            # reload gnome themes
            self.loadGdmThemes()
            dlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            print(_("Import Cancelled..."))
            dlg.destroy()

    def on_buttonSoftwareApply_clicked(self, widget):
        # customize distro
        warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
        warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        warnDlg.set_icon_from_file(self.iconFile)
        warnDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label()
        warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lblContinueText = _("  <b>Continue?</b>  ")
        lblContinueInfo = _("     This may take a few minutes.  Please wait...     ")
        label = Gtk.Label()
        label.set_text(lblContinueText)
        lblInfo = Gtk.Label()
        lblInfo.set_text(lblContinueInfo)
        label.set_use_markup(True)
        warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
        warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
        lblInfo.show()
        label.show()
        #warnDlg.show()
        response = warnDlg.run()
        if response == Gtk.ResponseType.OK:
            warnDlg.destroy()
            self.setBusyCursor()
            GLib.idle_add(self.customize)
            self.run_generator(self.calculateIsoSize)
        else:
            warnDlg.destroy()

    def on_buttonSoftwareCalculateIsoSize_clicked(self, widget):
        self.setBusyCursor()
        self.run_generator(self.calculateIsoSize)

    def on_buttonAltIsoCalculate_clicked(self, widget):
        self.setBusyCursor()
        self.run_generator(self.calculateAltIsoSize)

    def on_buttonInteractiveEditLaunch_clicked(self, widget):
        self.startInteractiveEdit()

    def on_buttonInteractiveClear_clicked(self, widget):
        warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
        warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        warnDlg.set_icon_from_file(self.iconFile)
        warnDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lblContinueText = _("  <b>Delete?</b>  ")
        label = Gtk.Label(lblContinueText)
        label.set_use_markup(True)
        warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
        label.show()
        #warnDlg.show()
        response = warnDlg.run()
        if response == Gtk.ResponseType.OK:
            warnDlg.destroy()
            self.setBusyCursor()
            # clear settings
            GLib.idle_add(self.clearInteractiveSettings)
        else:
            warnDlg.destroy()


    def on_buttonOptimizeShutdownRestore_clicked(self, widget):
        self.setBusyCursor()
        GLib.idle_add(self.restoreShutdown)

    def on_checkbuttonOptimizationStartupEnable_toggled(self, widget):
        if self.builder.get_object("checkbuttonOptimizationStartupEnable").get_active() == True:
            self.builder.get_object("labelOptimizationStartupInfo").show()
            self.builder.get_object("tableOptimizationStartup").show()
        else:
            self.builder.get_object("labelOptimizationStartupInfo").hide()
            self.builder.get_object("tableOptimizationStartup").hide()

    def on_buttonCustomizeLaunchTerminal_clicked(self, widget):
        self.launchTerminal()

    def on_buttonCustomizeLaunchChrootX_clicked(self, widget):
        self.doneTerminal()
        self.launchChrootXephyr()

    def on_buttonBurnIso_clicked(self, widget):
        # check for disc type
        if self.discType == 'live':
            self.burnIso()
        elif self.discType == 'alt':
            self.burnAltIso()
        else:
            print(_("Error: Cannot burn iso... Unknown disc type..."))

    def on_buttonCheckUpdates_clicked(self, widget):
        self.setBusyCursor()
        GLib.idle_add(self.checkForUpdates)

    def on_buttonModulesAddModule_clicked(self, widget):
        # filter only tar.gz files
        dlgFilter = Gtk.FileFilter()
        dlgFilter.set_name("Modules (.rmod)")
        dlgFilter.add_pattern("*.rmod")
        # create dialog
        dlgTitle = _('Select Reconstructor Module')
        dlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dlg.add_filter(dlgFilter)
        dlg.set_select_multiple(False)
        response = dlg.run()
        if response == Gtk.ResponseType.OK :
            self.addModule(dlg.get_filename())
            dlg.destroy()
        elif response == Gtk.ResponseType.CANCEL :
            print(_("Module installation cancelled..."))
            dlg.destroy()

    def on_buttonModulesViewModule_clicked(self, widget, treeview):
        self.showModuleSource(treeview)

    def on_buttonModulesUpdateModule_clicked(self, widget, treeview):
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        modName = ''
        modVersion = ''
        modPath = None
        modUpdateUrl = ''
        if iter:
            path = model.get_path(iter)
            modName = model.get_value(iter, self.moduleColumnName)
            modVersion = model.get_value(iter, self.moduleColumnVersion)
            modPath = model.get_value(iter, self.moduleColumnPath)
            modUpdateUrl = model.get_value(iter, self.moduleColumnUpdateUrl)
        # check for valid module and update
        if modPath != None:
            self.setBusyCursor()
            GLib.idle_add(self.updateModule, modName, modVersion, modPath, modUpdateUrl, treeview)

    def on_buttonModulesClearRunOnBoot_clicked(self, widget):
        warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
        warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.OK)
        warnDlg.set_icon_from_file(self.iconFile)
        warnDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lblContinueText = _("  <b>Clear all run on boot modules?</b>  ")
        label = Gtk.Label(lblContinueText)
        label.set_use_markup(True)
        warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
        label.show()
        #warnDlg.show()
        response = warnDlg.run()
        if response == Gtk.ResponseType.OK:
            warnDlg.destroy()
            # clear run on boot modules
            self.clearRunOnBootModules()
        else:
            warnDlg.destroy()

    def on_buttonBrowseAltWorkingDir_clicked(self, widget):
        dlgTitle = _('Select Working Directory')
        workingDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.SELECT_FOLDER)
        workingDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        workingDlg.set_uri(os.environ['HOME'] + '/reconstructor')
        response = workingDlg.run()
        if response == Gtk.ResponseType.OK :
            filename = workingDlg.get_current_folder()
            self.builder.get_object("entryAltWorkingDir").set_text(workingDlg.get_filename())
            workingDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            workingDlg.destroy()

    def on_buttonBrowseAltIsoFilename_clicked(self, widget):
        # filter only iso files
        isoFilter = Gtk.FileFilter()
        isoFilter.set_name("ISO Files (.iso)")
        isoFilter.add_pattern("*.iso")
        # create dialog
        dlgTitle = _('Select Alternate CD ISO')
        isoDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        isoDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        isoDlg.add_filter(isoFilter)
        isoDlg.set_current_folder(os.environ['HOME'])
        response = isoDlg.run()
        if response == Gtk.ResponseType.OK :
            self.builder.get_object("entryAltIsoFilename").set_text(isoDlg.get_filename())
            isoDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            isoDlg.destroy()

    def on_checkbuttonAltCreateRemasterDir_clicked(self, widget):
        if self.builder.get_object("checkbuttonAltCreateRemasterDir").get_active() == True:
            self.builder.get_object("hboxAltBase").set_sensitive(True)
        else:
            self.builder.get_object("hboxAltBase").set_sensitive(False)
    def on_buttonAptRepoImportGpgKey_clicked(self, widget):
        # filter only iso files
        gpgFilter = Gtk.FileFilter()
        gpgFilter.set_name("GPG Key Files (.gpg, .key)")
        gpgFilter.add_pattern("*.gpg")
        # create dialog
        dlgTitle = _('Select GPG Key File')
        gpgDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)
        gpgDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        gpgDlg.add_filter(gpgFilter)
        gpgDlg.set_current_folder(os.environ['HOME'])
        response = gpgDlg.run()
        if response == Gtk.ResponseType.OK :
            print(_('Importing GPG Key...'))
            try:
                subprocess.getoutput('cp -Rf \"' + gpgDlg.get_filename() + '\" \"' + os.path.join(self.customDir, "root") + '/tmp/apt_key.gpg\"')
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-key add /tmp/apt_key.gpg')
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root") + '/tmp/apt_key.gpg\"')
                print(_('GPG Key successfully imported...'))
            except Exception as detail:
                errImport = _('Error importing GPG key: ')
                print(errImport, detail)
                pass
            gpgDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            gpgDlg.destroy()

    def on_buttonAltPackagesImportGpgKey_clicked(self, widget):
        # filter only iso files
        gpgFilter = Gtk.FileFilter()
        gpgFilter.set_name("GPG Key Files (.gpg, .key)")
        gpgFilter.add_pattern("*.gpg")
        # create dialog
        dlgTitle = _('Select GPG Key File')
        gpgDlg = Gtk.FileChooserDialog(title=dlgTitle, parent=self.builder.get_object("windowMain"), action=Gtk.FileChooserAction.OPEN)    
        gpgDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        gpgDlg.add_filter(gpgFilter)
        gpgDlg.set_current_folder(os.environ['HOME'])
        response = gpgDlg.run()
        if response == Gtk.ResponseType.OK :
            print(_('Importing GPG Key...'))
            try:
                subprocess.getoutput('apt-key add \"' + gpgDlg.get_filename() + '\"')
                print(_('GPG Key successfully imported...'))
            except Exception as detail:
                errImport = _('Error importing GPG key: ')
                print(errImport, detail)
                pass
            gpgDlg.hide()
        elif response == Gtk.ResponseType.CANCEL :
            gpgDlg.destroy()

    def on_buttonAltPackagesApply_clicked(self, widget):
        # customize alternate
        warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
        warnDlg.add_buttons(Gtk.STOCK_NO, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        warnDlg.set_icon_from_file(self.iconFile)
        warnDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(" ")
        warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        lblContinueText = _("  <b>Continue?</b>  ")
        lblContinueInfo = _("     This may take a few minutes.  Please wait...     ")
        label = Gtk.Label(lblContinueText)
        lblInfo = Gtk.Label(lblContinueInfo)
        label.set_use_markup(True)
        warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
        warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
        lblInfo.show()
        label.show()
        #warnDlg.show()
        response = warnDlg.run()
        if response == Gtk.ResponseType.OK:
            warnDlg.destroy()
            self.setBusyCursor()
            GLib.idle_add(self.customizeAlt)
        else:
            warnDlg.destroy()


    def on_buttonDonate_clicked(self, widget):
        # go to web to donate
        if subprocess.getoutput('which firefox') != '':
            user = os.getlogin()
            subprocess.getoutput('su ' + user + ' firefox \"' + self.donateUrl + '\"')
        else:
            print(_("Cannot find system web browser.  Please copy and paste the following link in your browser."))
            print(self.donateUrl)
            print("")

    def saveSetupInfo(self):
        # do setup - check and create dirs as needed
        print(_("INFO: Saving working directory information..."))
        self.customDir = self.builder.get_object("entryWorkingDir").get_text()
        self.createRemasterDir = self.builder.get_object("checkbuttonCreateRemaster").get_active()
        self.createCustomRoot = self.builder.get_object("checkbuttonCreateRoot").get_active()
        self.createInitrdRoot = self.builder.get_object("checkbuttonCreateInitRd").get_active()
        # debug
        print("Custom Directory: " + str(self.customDir))
        print("Create Remaster Directory: " + str(self.createRemasterDir))
        print("Create Custom Root: " + str(self.createCustomRoot))
        print("Create Initrd Root: " + str(self.createInitrdRoot))
 
    def saveAltSetupInfo(self):
        # do setup - check and create dirs as needed
        print(_("INFO: Saving working directory information..."))
        self.customDir = self.builder.get_object("entryAltWorkingDir").get_text()
        self.createAltRemasterDir = self.builder.get_object("checkbuttonAltCreateRemasterDir").get_active()
        self.createAltInitrdRoot = self.builder.get_object("checkbuttonAltCreateInitrdDir").get_active()
        # debug
        print("Custom Directory: " + str(self.customDir))
        print("Create Remaster Directory: " + str(self.createAltRemasterDir))
        print("Create Initrd Root: " + str(self.createAltInitrdRoot))


# ---------- Setup ---------- #
    def setupWorkingDirectory(self):
        print(_("INFO: Setting up working directory..."))
        self.showProgress(_("Setting up working directory..."),0.05)
        yield True
        self.setBusyCursor()
        # remaster dir
        self.isoFilename = self.builder.get_object("entryIsoFilename").get_text()
        print('ISO File:' + self.isoFilename)
        if self.createRemasterDir == True:
            # check for existing directories and remove if necessary
            #if os.path.exists(os.path.join(self.customDir, "remaster")):
            #    print(_("INFO: Removing existing Remaster directory..."))
            #    subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/") + '\"')
            if os.path.exists(os.path.join(self.customDir, "remaster")) == False:
                print("INFO: Creating Remaster directory...")
                os.makedirs(os.path.join(self.customDir, "remaster"))
            # check for iso
            if  self.isoFilename == "":
                mntDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                mntDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
                mntDlg.set_icon_from_file(self.iconFile)
                mntDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                mntDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblText = _("  <b>Please insert Ubuntu Live CD and click OK</b>  ")
                label = Gtk.Label(lblText)
                label.set_use_markup(True)
                mntDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                label.show()
                #warnDlg.show()
                response = mntDlg.run()
                if response == Gtk.ResponseType.OK:
                    print(_("Using Live CD for remastering..."))
                    mntDlg.destroy()
                    subprocess.getoutput("mount " + self.mountDir)
                else:
                    mntDlg.destroy()
                    self.setDefaultCursor()
                    return
            else:
                print(_("Using ISO for remastering..."))
                subprocess.getoutput('mount -o loop \"' + self.isoFilename + '\" ' + self.mountDir)

            print(_("Copying files..."))
            self.showProgress(_("Copying files..."),0.06)
            yield True
            # copy remaster files
            self.setBusyCursor()
            subprocess.getoutput('rsync -at --del ' + self.mountDir + '/ \"' + os.path.join(self.customDir, "remaster") + '\"')
            print(_("Finished copying files..."))
            self.showProgress(_("Finished copying files..."),0.10)
            yield True
            # unmount iso/cd-rom
            subprocess.getoutput("umount " + self.mountDir)
        # call doneTerminal to umount all direcotry that mounted
        self.doneTerminal(forceMode=True,silentMode=False,justUmount=False)
        # custom root dir
        if self.createCustomRoot == True:
            #if os.path.exists(os.path.join(self.customDir, "root")):
            #    print(_("INFO: Removing existing Custom Root directory..."))

            #    subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/") + '\"')
            if os.path.exists(os.path.join(self.customDir, "root")) == False:
                print(_("INFO: Creating Custom Root directory..."))
                os.makedirs(os.path.join(self.customDir, "root"))
            # check for existing directories and remove if necessary
            if os.path.exists(os.path.join(self.customDir, "tmpsquash")):
                print(_("INFO: Removing existing tmpsquash directory..."))

                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "tmpsquash") + '\"')

            # extract squashfs into custom root
            # check for iso
            if self.isoFilename == "":
                mntDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                mntDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
                mntDlg.set_icon_from_file(self.iconFile)
                mntDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                mntDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblText = _("  <b>Please insert Ubuntu Live CD and click OK</b>  ")
                label = Gtk.Label(lblText)
                label.set_use_markup(True)
                mntDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                label.show()
                response = mntDlg.run()
                if response == Gtk.ResponseType.OK:
                    print(_("Using Live CD for squashfs root..."))
                    mntDlg.destroy()
                    subprocess.getoutput("mount " + self.mountDir)
                else:
                    mntDlg.destroy()
                    self.setDefaultCursor()
                    return
            else:
                print(_("Using ISO for squashfs root..."))
                subprocess.getoutput('mount -o loop \"' + self.isoFilename + '\" ' + self.mountDir)

            # copy remaster files
            os.mkdir(os.path.join(self.customDir, "tmpsquash"))
            # mount squashfs root
            print(_("Mounting squashfs..."))
            subprocess.getoutput('mount -t squashfs -o loop ' + self.mountDir + '/casper/filesystem.squashfs \"' + os.path.join(self.customDir, "tmpsquash") + '\"')
            print(_("Extracting squashfs root..."))
            self.showProgress(_("Extracting squashfs root..."),0.10)
            yield True
            # copy squashfs root
            self.setBusyCursor()
            subprocess.getoutput('rsync -at --del \"' + os.path.join(self.customDir, "tmpsquash") + '\"/ \"' + os.path.join(self.customDir, "root/") + '\"')
            # umount tmpsquashfs
            print(_("Unmounting tmpsquash..."))
            subprocess.getoutput('umount -lf \"' + os.path.join(self.customDir, "tmpsquash") + '\"')
            # umount cdrom
            print(_("Unmounting cdrom..."))
            subprocess.getoutput("umount -lf " + self.mountDir)
            # remove tmpsquash
            print(_("Removing tmpsquash..."))
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "tmpsquash") + '\"')
            # set proper permissions - MUST DO WITH UBUNTU
            print(_("Setting proper permissions..."))
            subprocess.getoutput('chmod 6755 \"' + os.path.join(self.customDir, "root/usr/bin/sudo") + '\"')
            subprocess.getoutput('chmod 0440 \"' + os.path.join(self.customDir, "root/etc/sudoers") + '\"')
            print(_("Checking chroot kernel file if exists..."))
            self.checkChroot()
            print(_("Finished extracting squashfs root..."))
            self.showProgress(_("Finished extracting squashfs root..."),0.18)
            yield True
        # initrd dir
        if self.createInitrdRoot == True:
            if os.path.exists(os.path.join(self.customDir, "initrd")):
                print(_("INFO: Removing existing Initrd directory..."))
                subprocess.getoutput('rm -Rf ' + os.path.join(self.customDir, "initrd"))
            print(_("INFO: Creating Initrd directory..."))
            os.makedirs(os.path.join(self.customDir, "initrd"))
            # check for iso
            if self.isoFilename == "":
                mntDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                mntDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
                mntDlg.set_icon_from_file(self.iconFile)
                mntDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                mntDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblText = _("  <b>Please insert Ubuntu Live CD and click OK</b>  ")
                label = Gtk.Label(lblText)
                label.set_use_markup(True)
                mntDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                label.show()
                response = mntDlg.run()
                if response == Gtk.ResponseType.OK:
                    print(_("Using Live CD for initrd..."))
                    mntDlg.destroy()
                    subprocess.getoutput("mount " + self.mountDir)
                else:
                    mntDlg.destroy()
                    self.setDefaultCursor()
                    yield False
            else:
                print(_("Using ISO for initrd..."))
                subprocess.getoutput('mount -o loop \"' + self.isoFilename + '\" ' + self.mountDir)

            # extract initrd
            print(_("Extracting Initial Ram Disk (initrd)..."))
            self.showProgress(_("Extracting Initial Ram Disk (initrd)..."),0.18)
            yield True
            self.setBusyCursor()
            initramfile=subprocess.getoutput("grep \"initrd=/casper/\" -Ir " + os.path.join(self.mountDir,"isolinux") + " | head -n 1 | sed -e \"s/.*initrd=\/casper\/\(\w\+\).*/\\1/g\"")
            if (os.path.exists(os.path.join(self.mountDir ,'casper', initramfile))):
                subprocess.getoutput('unmkinitramfs ' + os.path.join(self.mountDir ,'casper', initramfile) + ' ' + os.path.join(self.customDir, "initrd"))

            # umount cdrom
            subprocess.getoutput("umount " + self.mountDir)

        # get ubuntu version
        self.loadCdVersion()
        if apt_pkg.version_compare(self.cdUbuntuVersion, '14.04') >= 0:
             self.builder.get_object("notebookCustomize").hide()
             self.builder.get_object("vboxCustomizeLive").show()
        else:
             self.builder.get_object("notebookCustomize").show()
             self.builder.get_object("vboxCustomizeLive").hide()
             # get current boot options menu text color
             self.loadBootMenuColor()
             # get current gdm background color
             self.loadGdmBackgroundColor()
             # load comboboxes for customization
             self.loadGdmThemes()
             self.loadGnomeThemes()
        #self.hideWorking()
        self.setDefaultCursor()
        self.setPage(self.pageLiveCustomize)
        print(_("Finished setting up working directory..."))
        print(" ")
        self.showProgress(_('Finished setting up working directory...'),0.20)
        self.run_generator(self.calculateIsoSize)
        yield False

    def setupAltWorkingDirectory(self):
        print(_("INFO: Setting up alternate working directory..."))
        self.showProgress(_("Setting up alternate working directory..."),0.05)
        yield True
        # remaster dir
        if self.createAltRemasterDir == True:
            # check for existing directories and remove if necessary
            #if os.path.exists(os.path.join(self.customDir, self.altRemasterDir)):
            #    print(_("INFO: Removing existing Alternate Remaster directory..."))
            #    subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
            #    os.makedirs(os.path.join(self.customDir, self.altRemasterDir))
            if os.path.exists(os.path.join(self.customDir, self.altRemasterDir)) == False:
                # create remaster dir
                os.makedirs(os.path.join(self.customDir, self.altRemasterDir))

            # only create if doesn't exists -- keep existing and use rsync for speed
            # check for tmp package dir
            #if os.path.exists(os.path.join(self.customDir, self.tmpPackageDir)) == False:
                # create tmp package dir
            #    os.makedirs(os.path.join(self.customDir, self.tmpPackageDir))

            # create tmp dir
            if os.path.exists(os.path.join(self.customDir, self.tmpDir)) == False:
                # create tmp dir
                os.makedirs(os.path.join(self.customDir, self.tmpDir))
            else:
                # clean tmp dir
                print(_("Cleaning alternate temporary directory..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                subprocess.getoutput('rm -Rf ./*')
            # create archives/partial dir
            #if os.path.exists(os.path.join(os.path.join(self.customDir, self.tmpPackageDir), "archives/partial")) == False:
            #    os.makedirs(os.path.join(os.path.join(self.customDir, self.tmpPackageDir), "archives/partial"))
            # create alt remaster repo
            if os.path.exists(os.path.join(self.customDir, self.altRemasterRepo)) == False:
                # create alternate remaster repo
                os.makedirs(os.path.join(self.customDir, self.altRemasterRepo))
            #print("INFO: Creating Remaster directory...")
            # check for iso
            self.isoFilename = self.builder.get_object("entryAltIsoFilename").get_text()
            print('ISO File:' + self.isoFilename)
            if self.isoFilename == "":
                mntDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                mntDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
                mntDlg.set_icon_from_file(self.iconFile)
                mntDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                mntDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblText = _("  <b>Please insert Ubuntu Alternate CD and click OK</b>  ")
                label = Gtk.Label(lblText)
                label.set_use_markup(True)
                mntDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                label.show()
                #warnDlg.show()
                response = mntDlg.run()
                if response == Gtk.ResponseType.OK:
                    print(_("Using Alternate CD for remastering..."))
                    mntDlg.destroy()
                    subprocess.getoutput("mount " + self.mountDir)
                else:
                    mntDlg.destroy()
                    self.setDefaultCursor()
                    yield False
            else:
                print(_("Using ISO for remastering..."))
                subprocess.getoutput('mount -o loop \"' + self.isoFilename + '\" ' + self.mountDir)

            # copy remaster files
            print(_("Copying alternate remaster directory..."))
            self.showProgress(_("Copying alternate remaster directory..."),0.08)
            yield True
            #subprocess.getoutput('rsync -at --del --exclude=\"pool/main/**/*.deb\" --exclude=\"pool/restricted/**/*.deb\" ' + self.mountDir + '/ \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
            self.setBusyCursor()
            subprocess.getoutput('rsync -at --del ' + self.mountDir + '/ \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
            self.showProgress(False,0.20)
            yield True

            # ----- Removed due to poor ubuntu dependency packaging -----
            # copy alternate base
            #baseType = self.builder.get_object("comboboxAltBase").get_active()
            #print(_("Copying files..."))
            #typeTxt = _("Using Alternate Base:")
            ## HACK: use rsync to find packages and copy
            #if baseType == self.altBaseTypeStandard:
            #    print(typeTxt,"Standard")
            #    pHelper.copyPackages(pHelper.ubuntuMinimalPackages, self.mountDir + '/', os.path.join(self.customDir, self.altRemasterDir))
            #elif baseType == self.altBaseTypeServer:
            #    print(typeTxt, " Server")
            #    pHelper.copyPackages(pHelper.ubuntuServerPackages, self.mountDir + '/', os.path.join(self.customDir, self.altRemasterDir))
            #elif baseType == self.altBaseTypeDesktop:
            #    print(typeTxt, " Desktop")
            #    pHelper.copyPackages(pHelper.ubuntuDesktopPackages, self.mountDir + '/', os.path.join(self.customDir, self.altRemasterDir))
            #else:
            #    print(_("ERROR: Unknown Alternate Base Type..."))

            print(_("Finished copying files..."))

            # unmount iso/cd-rom
            subprocess.getoutput("umount " + self.mountDir)
        # initrd dir
        if self.createAltInitrdRoot == True:
            if os.path.exists(os.path.join(self.customDir, self.altInitrdRoot)):
                print(_("INFO: Removing existing Alternate Initrd directory..."))
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, self.altInitrdRoot) + '\"')
            print(_("INFO: Creating Alternate Initrd directory..."))
            os.makedirs(os.path.join(self.customDir, self.altInitrdRoot))
            # check for iso
            if self.isoFilename == "":
                mntDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
                mntDlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
                mntDlg.set_icon_from_file(self.iconFile)
                mntDlg.vbox.set_spacing(10)
                labelSpc = Gtk.Label(" ")
                mntDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
                labelSpc.show()
                lblText = _("  <b>Please insert Ubuntu Alternate CD and click OK</b>  ")
                label = Gtk.Label(lblText)
                label.set_use_markup(True)
                mntDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
                label.show()
                response = mntDlg.run()
                if response == Gtk.ResponseType.OK:
                    print(_("Using Alternate CD for initrd..."))
                    mntDlg.destroy()
                    subprocess.getoutput("mount " + self.mountDir)
                else:
                    mntDlg.destroy()
                    self.setDefaultCursor()
                    yield False
            else:
                print(_("Using ISO for initrd..."))
                subprocess.getoutput('mount -o loop \"' + self.isoFilename + '\" ' + self.mountDir)

            # extract initrd
            print(_("Extracting Alternate Initial Ram Disk (initrd)..."))
            self.showProgress(_("Extracting Alternate Initial Ram Disk (initrd)..."),0.22)
            yield True
            self.setBusyCursor()
            if (os.path.exists(self.mountDir + '/install/initrd.lz')):
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altInitrdRoot) + '\"')
                subprocess.getoutput('cat ' + self.mountDir + '/install/initrd.lz | lzma -d | cpio -i')
            elif (os.path.exists(self.mountDir + '/install/initrd.gz')):
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altInitrdRoot) + '\"')
                subprocess.getoutput('cat ' + self.mountDir + '/install/initrd.gz | gzip -d | cpio -i')
            elif (os.path.exists(self.mountDir + '/install/initrd')):
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altInitrdRoot) + '\"')
                subprocess.getoutput('cat ' + self.mountDir + '/install/initrd | gzip -d | cpio -i')
            self.showProgress(False,0.30)
            yield True

            # umount cdrom
            subprocess.getoutput("umount " + self.mountDir)


        self.setDefaultCursor()
        # calculate iso size in the background
        self.run_generator(self.calculateAltIsoSize)
        print(_("Finished setting up alternate working directory..."))
        print(" ")
        yield False

    def liveCDKernel(self):
        subprocess.getoutput('rm -Rf ' + os.path.join(self.customDir, "root/boot/initrd.live"))
        subprocess.getoutput('rm -Rf ' + os.path.join(self.customDir, "root/boot/initrd_live"))
        kver=find_newest_kernel_version(os.path.join(self.customDir, "root/boot"))
        casper_initram_file=subprocess.getoutput("grep \"initrd=/casper/\" -Ir " + os.path.join(self.customDir,'remaster','isolinux') + " | head -n 1 | sed -e \"s/.*initrd=\/casper\/\(\w\+\).*/\\1/g\"")
        casper_kernel_file=subprocess.getoutput("grep \"initrd=/casper/\" -Ir " + os.path.join(self.customDir,'remaster','isolinux') + " | head -n 1 | sed -e \"s/.*kernel\W\+\/casper\/\(\w\+\).*/\\1/g\"")
        if kver != '' and os.path.exists(os.path.join(self.customDir,"root/boot/initrd.img-" + kver)):
            os.makedirs(os.path.join(self.customDir, "root/boot/initrd.live"))
            if os.path.exists(os.path.join(self.customDir, 'remaster', 'casper', casper_initram_file)):
                subprocess.getoutput('cp -f \"' + os.path.join(self.customDir,"root/boot/initrd.img-" + kver) + '\" \"' + os.path.join(self.customDir, "remaster/casper/", casper_initram_file) + '\"')
                subprocess.getoutput('unmkinitramfs ' + self.customDir + '/remaster/casper/' + casper_initram_file + ' ' + os.path.join(self.customDir, "root/boot/initrd.live"))
            if os.path.exists(os.path.join(self.customDir,"initrd/main")):
                subprocess.getoutput('cp -dR \"' + os.path.join(self.customDir, "initrd/main/conf/*") + ' ' + os.path.join(self.customDir, "root/boot/initrd.live/main/conf/"))
                subprocess.getoutput('cp -dR \"' + os.path.join(self.customDir, "initrd/main/etc/*") + ' ' + os.path.join(self.customDir, "root/boot/initrd.live/main/etc/"))
                subprocess.getoutput('cp -dR \"' + os.path.join(self.customDir, "initrd/main/scripts") + ' ' + os.path.join(self.customDir, "root/boot/initrd.live/main/conf/"))
                subprocess.getoutput('mount -t proc none \"' + os.path.join(self.customDir, "root/proc") + '\"')
                subprocess.getoutput('chroot ' + os.path.join(self.customDir, 'root') \
                    + ' mkinitramfs -d boot/initrd.live/main/conf -o boot/initrd_live')
                subprocess.getoutput('umount \"' + os.path.join(self.customDir, "root/proc") + '\"')
                if os.path.exists(os.path.join(self.customDir, 'root/boot/initrd_live')):
                    subprocess.getoutput('cp -f \"' + os.path.join(self.customDir,"root/boot/initrd_live") + '\" \"' + os.path.join(self.customDir, "remaster/casper", casper_kernel_file) + '\"')
                subprocess.getoutput('rm -rf \"' + os.path.join(self.customDir,"root/boot/initrd.live") + '\"')
                subprocess.getoutput('rm -f \"' + os.path.join(self.customDir,"root/boot/initrd_live") + '\"')
        if kver != '' and os.path.exists(os.path.join(self.customDir,"root/boot/vmlinuz-" + kver)):
            if (os.path.exists(os.path.join(self.customDir,"remaster/casper", casper_kernel_file))):
                subprocess.getoutput('cp -f \"' + os.path.join(self.customDir,"root/boot/vmlinuz-" + kver) + '\" \"' + os.path.join(self.customDir, "remaster/casper", casper_kernel_file) + '\"')

    def getTerminal(self):
        try:
            terminal = os.environ["COLORTERM"]
        except:
            terminal = 'gnome-terminal'

        if subprocess.getoutput('which ' + terminal) != '':
            pass
        elif subprocess.getoutput('which gnome-terminal') != '':
            terminal = 'gnome-terminal'
        elif subprocess.getoutput('which mate-terminal') != '':
            terminal = 'mate-terminal'
        elif subprocess.getoutput('which konsole') != '':
            terminal = 'konsole'
        elif subprocess.getoutput('which xfc4-terminal') != '':
            terminal = 'xfc4-terminal'
        elif subprocess.getoutput('which lxterminal') != '':
            terminal = 'lxterminal'
        elif subprocess.getoutput('which qterminal') != '':
            terminal = 'qterminal'
        return terminal

# ---------- Customize Live ---------- #
    def customize(self):
        print(_("INFO: Customizing..."))
        # check user entered password first, so user doesn't have to wait
        if self.checkUserPassword() == False:
            print(_('User passwords do not match.'))
            # show warning dlg
            warnDlg = Gtk.Dialog(title=self.appName, parent=None, flags=0)
            warnDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
            warnDlg.set_icon_from_file(self.iconFile)
            warnDlg.vbox.set_spacing(10)
            labelSpc = Gtk.Label(" ")
            warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
            labelSpc.show()
            lblBuildText = _("  <b>Passwords do not match</b>  ")
            lblBuildInfo = _("     Please make sure passwords match and try again...     ")
            label = Gtk.Label(lblBuildText)
            lblInfo = Gtk.Label(lblBuildInfo)
            label.set_use_markup(True)
            warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
            warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
            lblInfo.show()
            label.show()
            response = warnDlg.run()
            # destroy dialog no matter what...
            if response == Gtk.ResponseType.OK:
                warnDlg.destroy()
            else:
                warnDlg.destroy()
            # show live cd customization page
            self.builder.get_object("notebookCustomize").set_current_page(-1)
            # return - don't continue until error fixed
            return

        # boot customization
        # live cd text color
        if apt_pkg.version_compare(self.cdUbuntuVersion, '14.04') < 0 \
                and os.path.exists(os.path.join(self.customDir, "remaster/isolinux/isolinux.cfg")):
            print(_("Setting Live CD Text color..."))
            color = self.builder.get_object("colorbuttonBrowseLiveCdTextColor").get_rgba().to_color()
            rgbColor = color.red//255, color.green//255, color.blue//255
            hexColor = '%02x%02x%02x' % rgbColor
            # replace config line in isolinux.cfg
            f = open(os.path.join(self.customDir, "remaster/isolinux/isolinux.cfg"), 'r')
            lines = []
            r = re.compile('GFXBOOT-BACKGROUND*', re.IGNORECASE)
            # find config string
            for line in f:
                if r.search(line) != None:
                    # replace
                    line = 'GFXBOOT-BACKGROUND 0x' + str(hexColor) + '\n'
                lines.append(line)

            f.close()
            # re-write config file
            f = open(os.path.join(self.customDir, "remaster/isolinux/isolinux.cfg"), 'w')
            f.writelines(lines)
            f.close()

        # LiveCD kernel
        if  self.builder.get_object("checkbuttonLiveCdUpdateKernel").get_active() == True:
            print(_("Updating LiveCD Linux kernel..."))
            self.liveCDKernel()
            #Intentionally reset the GUI checkbutton in case the user clicks apply again.
            self.builder.get_object("checkbuttonLiveCdUpdateKernel").set_active(False)
        # LiveCD info must be set afterwards in case the user updates the kernel as the initrd folder is replaced
        if self.checkUserPassword() == True:
            # set user info
            user = self.builder.get_object("entryLiveCdUsername").get_text()
            userFull = self.builder.get_object("entryLiveCdUserFullname").get_text()
            password = self.builder.get_object("entryLiveCdUserPassword").get_text()
            host = self.builder.get_object("entryLiveCdHostname").get_text()
            # set live cd info
            self.setLiveCdInfo(username=user, userFullname=userFull, userPassword=password, hostname=host)
        # wallpaper
        if self.builder.get_object("entryGnomeDesktopWallpaperFilename").get_text() != "":
            print(_("Customizing Gnome wallpaper..."))
            path, filename = os.path.split(self.builder.get_object("entryGnomeDesktopWallpaperFilename").get_text())
            subprocess.getoutput('cp -f \"' + self.builder.get_object("entryGnomeDesktopWallpaperFilename").get_text() + '\" \"' + os.path.join(self.customDir, "root/usr/share/backgrounds/") + filename + '\"')
            subprocess.getoutput('chmod 777 \"' + os.path.join(self.customDir, "root/usr/share/backgrounds/") + filename + '\"')
            # set wallpaper in gconf
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /desktop/gnome/background/picture_filename \"/usr/share/backgrounds/' + filename + '\"')
        # set fonts in gconf
        if self.builder.get_object("labelGnomeDesktopApplicationFontValue").get_text() != "":
            print(_("Setting Gnome application font..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /desktop/gnome/interface/font_name \"' + self.builder.get_object("labelGnomeDesktopApplicationFontValue").get_text() + '\"')
        if self.builder.get_object("labelGnomeDesktopDocumentFontValue").get_text() != "":
            print(_("Setting Gnome document font..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /desktop/gnome/interface/document_font_name \"' + self.builder.get_object("labelGnomeDesktopDocumentFontValue").get_text() + '\"')
        if self.builder.get_object("labelGnomeDesktopFontValue").get_text() != "":
            print(_("Setting Gnome desktop font..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /apps/nautilus/preferences/desktop_font \"' + self.builder.get_object("labelGnomeDesktopFontValue").get_text() + '\"')
        if self.builder.get_object("labelGnomeDesktopTitleBarFontValue").get_text() != "":
            print(_("Setting Gnome title bar font..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /apps/metacity/general/titlebar_font \"' + self.builder.get_object("labelGnomeDesktopTitleBarFontValue").get_text() + '\"')
        if self.builder.get_object("labelGnomeDesktopFixedFontValue").get_text() != "":
            print(_("Setting Gnome fixed font..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /desktop/gnome/interface/monospace_font_name \"' + self.builder.get_object("labelGnomeDesktopFixedFontValue").get_text() + '\"')

        # set theme options in gconf
        # theme
        if self.builder.get_object("comboboxentryGnomeTheme").get_active_id() != "" \
                and self.builder.get_object("comboboxentryGnomeTheme").get_active_id() != None:
            print(_("Setting Gnome theme..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /desktop/gnome/interface/gtk_theme \"' + self.builder.get_object("comboboxentryGnomeTheme").get_active_id() + '\"')
        # window borders
        if self.builder.get_object("comboboxentryGnomeThemeWindowBorders").get_active_id() != "" \
                and self.builder.get_object("comboboxentryGnomeThemeWindowBorders").get_active_id() != None:
            print(_("Setting Gnome window borders..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /apps/metacity/general/theme \"' + self.builder.get_object("comboboxentryGnomeThemeWindowBorders").get_active_id() + '\"')
        # icons
        if self.builder.get_object("comboboxentryGnomeThemeIcons").get_active_id() != "" \
                and self.builder.get_object("comboboxentryGnomeThemeIcons").get_active_id() != None:
            print(_("Setting Gnome icons..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.defaults --type string --set /desktop/gnome/interface/icon_theme \"' + self.builder.get_object("comboboxentryGnomeThemeIcons").get_active_id() + '\"')

        # gdm configuration
        if self.checkCustomGdm() == True and os.path.exists(os.path.join(self.customDir, "root/etc/gdm/gdm.conf-custom")):
            print(_("Configuring GDM..."))
            conf = "[daemon]\nRemoteGreeter=/usr/lib/gdm/gdmgreeter\n\n"
            # security
            print(_("Setting GDM Security..."))
            if self.builder.get_object("checkbuttonGdmRootLogin").get_active() == True:
                conf = conf + "[security]\nAllowRoot=true\n\n"
            else:
                conf = conf + "[security]\nAllowRoot=false\n\n"
            # xdmcp
            print(_("Setting GDM XDMCP..."))
            if self.builder.get_object("checkbuttonGdmXdmcp").get_active() == True:
                conf = conf + "[xdmcp]\nEnable=true\n\n"
            else:
                conf = conf + "[xdmcp]\nEnable=false\n\n"
            conf = conf + "[gui]\n\n"
            conf = conf + "[greeter]\n"
            # gdm color
            color = self.builder.get_object("colorbuttonBrowseGdmBackgroundColor").get_rgba().to_color()
            rgbColor = color.red//255, color.green//255, color.blue//255
            hexColor = '%02x%02x%02x' % rgbColor
            conf += 'GraphicalThemedColor=#' + str(hexColor) + '\n'
            if self.builder.get_object("comboboxentryGnomeGdmTheme").get_active_id() != "" \
                 and self.builder.get_object("comboboxentryGnomeGdmTheme").get_active_id() != None:
                print(_("Setting GDM Theme..."))
                conf = conf + "GraphicalTheme=" + self.builder.get_object("comboboxentryGnomeGdmTheme").get_active_id() + "\n"
            print(_("Setting GDM Sounds..."))
            if self.builder.get_object("checkbuttonGdmSounds").get_active() == True:
                conf = conf + "SoundOnLogin=true\n\n"
            else:
                conf = conf + "SoundOnLogin=false\n\n"

            print(_("Backing up GDM configuration..."))
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/gdm/gdm.conf-custom") + '\" \"' + os.path.join(self.customDir, "root/etc/gdm/gdm.conf-custom.orig") + '\"')

            print(_("Saving GDM configuration..."))
            f=open(os.path.join(self.customDir, "root/etc/gdm/gdm.conf-custom"), 'w')
            f.write(conf)
            f.close()


        # set up apt repos
        if self.checkCustomRepos() == True:
            # move old sources.list apt file
            print(_("Backing up old apt config..."))
            subprocess.getoutput('mv -f ' + os.path.join(self.customDir, "root/etc/apt/sources.list") + ' ' + os.path.join(self.customDir, "root/etc/apt/sources.list.orig"))
            #subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/etc/apt/sources.list"))
            # load ubuntu codename for apt
            ubuntuCodename = ''
            if self.cdUbuntuVersion == self.dapperVersion:
                ubuntuCodename = 'dapper'
            elif self.cdUbuntuVersion == self.edgyVersion:
                ubuntuCodename = 'edgy'
            elif self.cdUbuntuVersion == self.feistyVersion:
                ubuntuCodename = 'feisty'
            elif self.cdUbuntuVersion == self.gutsyVersion:
                ubuntuCodename = 'gutsy'
            elif self.cdUbuntuVersion == self.hardyVersion:
                ubuntuCodename = 'hardy'
            elif self.cdUbuntuVersion == self.intrepidVersion:
                ubuntuCodename = 'intrepid'
            elif self.cdUbuntuVersion == self.jauntyVersion:
                ubuntuCodename = 'jaunty'
            elif self.cdUbuntuVersion == self.karmicVersion:
                ubuntuCodename = 'karmic'
            else:
                print(_("Unable to detect codename for Ubuntu CD Version - APT Repositories will NOT be modified..."))

            if ubuntuCodename != '':
                # ubuntu official
                if self.builder.get_object("checkbuttonAptRepoUbuntuOfficial").get_active() == True:
                    print(_("Adding Official Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + ubuntuCodename + ' main\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')
                    print(_('Adding Ubuntu Official Security Repository...'))
                    subprocess.getoutput('echo \"deb http://security.ubuntu.com/ubuntu ' + ubuntuCodename +'-security main restricted\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')
                    subprocess.getoutput('echo \"deb-src http://security.ubuntu.com/ubuntu ' + ubuntuCodename + '-security main restricted\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')

                # ubuntu restricted
                if self.builder.get_object("checkbuttonAptRepoUbuntuRestricted").get_active() == True:
                    print(_("Adding Ubuntu Restricted Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + ubuntuCodename + ' restricted\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')

                # ubuntu universe
                if self.builder.get_object("checkbuttonAptRepoUbuntuUniverse").get_active() == True:
                    print(_("Adding Ubuntu Universe Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + ubuntuCodename + ' universe\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')
                    print(_('Adding Ubuntu Universe Security Repository...'))
                    subprocess.getoutput('echo \"deb http://security.ubuntu.com/ubuntu ' + ubuntuCodename + '-security universe\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')
                    subprocess.getoutput('echo \"deb-src http://security.ubuntu.com/ubuntu ' + ubuntuCodename + '-security universe\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')

                # ubuntu multiverse
                if self.builder.get_object("checkbuttonAptRepoUbuntuMultiverse").get_active() == True:
                    print(_("Adding Ubuntu Multiverse Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + ubuntuCodename + ' multiverse\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')

                # ubuntu official updates
                print(_("Adding Ubuntu Official Updates Apt Repository..."))
                subprocess.getoutput('echo \"deb http://us.archive.ubuntu.com/ubuntu/ ' + ubuntuCodename + '-updates main restricted\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list") + '\"')

                # custom archives
                buf = self.builder.get_object("textviewAptCustomArchives").get_buffer()
                buflist = self.builder.get_object("textviewAptCustomSourcesList").get_buffer()
                if buf.get_text(buf.get_start_iter(),buf.get_end_iter()) != '':
                    print(_("Adding Custom Apt Repositories..."))
                    subprocess.getoutput('echo \"' + buf.get_text(buf.get_start_iter(),buf.get_end_iter()) + '\" >> \"' + os.path.join(self.customDir, "root/etc/apt/sources.list.d/" + buflist.get_text(buflist.get_start_iter(),buflist.get_end_iter())) + '\"')

        # interactive editing
        if self.interactiveEdit == True:
            # copy template user config to /etc/skel in root dir
            try:
                print(_('Removing existing template...'))
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/skel/*") + '\"')
                print(_('Copying User Template...'))
                subprocess.getoutput('cp -Rf /home/reconstructor ' + os.path.join(self.customDir, "root/etc/skel") )
                subprocess.getoutput('cp -Rf ' + os.path.join(self.customDir, "root/etc/skel/reconstructor/*") + ' ' + os.path.join(self.customDir, "root/etc/skel/"))
                subprocess.getoutput('rm -Rf ' + os.path.join(self.customDir, "root/etc/skel/reconstructor"))
            except Exception as detail:
                errCopy = _('Error copying template: ')
                print(errCopy, detail)
                pass
        # startup optimization
        if self.builder.get_object("checkbuttonOptimizationStartupEnable").get_active() == True:
            self.optimizeStartup()

        # shutdown optimization
        if self.builder.get_object("checkbuttonOptimizationShutdown").get_active() == True:
            self.optimizeShutdown()

        # run modules
        # HACK: check for run on boot scripts and clear previous if new ones selected
        self.execModulesEnabled = False;
        if self.treeModel != None:
            self.treeModel.foreach(self.checkExecModuleEnabled)
        if self.execModulesEnabled == True:
            print(_('Running modules...'))
            modExecScrChroot = '#!/bin/sh\n\napt-get update\ncd /tmp ;\n'
            # copy all "execute" enabled scripts proper location (chroot or customdir)
            self.treeModel.foreach(self.copyExecuteModule)
            # find all modules in chroot and chain together and run
            for execModRoot, execModexecModDirs, execModFiles in os.walk(os.path.join(self.customDir, "root/tmp/")):
                for execMod in execModFiles:
                    r, ext = os.path.splitext(execMod)
                    if ext == '.rmod':
                        modExecScrChroot += 'echo Running Module: ' + os.path.basename(execMod) + '\n'
                        modExecScrChroot += 'bash \"/tmp/' + os.path.basename(execMod) + '\"' + ' ;\n '
            modExecScrChroot += 'echo Cleaning Apt Cache...\n'
            modExecScrChroot += 'apt-get clean \n'
            modExecScrChroot += 'apt-get autoclean \n'
            modExecScrChroot += '\necho \'--------------------\'\necho \'Modules Finished...\'\n'
            modExecScrChroot += 'sleep 10'
            #modExecScrChroot += 'echo \'Press [Enter] to continue...\'\nread \n'
            #print(modExecScrChroot)
            fModExecChroot=open(os.path.join(self.customDir, "root/tmp/module-exec.sh"), 'w')
            fModExecChroot.write(modExecScrChroot)
            fModExecChroot.close()
            subprocess.getoutput('chmod a+x ' + os.path.join(self.customDir, "root/tmp/module-exec.sh"))
            #subprocess.getoutput('xterm -title \'Reconstructor Module Exec\' -e chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/module-exec.sh')
            # add current user to the access control list
            user = subprocess.getoutput('echo $USER')
            print(_("Adding user " + user + " to access control list..."))
            subprocess.getoutput('xhost +local:' + user)
            # copy dns info
            if os.path.exists("/etc/resolv.conf"):
                print(_("Copying DNS info..."))
                subprocess.getoutput('cp -L --remove-destination /etc/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            elif os.path.exists("/run/resolvconf/resolv.conf"):
                print(_("Copying DNS info..."))
                subprocess.getoutput('cp -L --remove-destination /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            # mount /proc
            print(_("Mounting /proc filesystem..."))
            subprocess.getoutput('mount -t proc none \"' + os.path.join(self.customDir, "root/proc") + '\"')
            #mount /var/run/dbus
            print(_("Mounting /var/run/dubs filesystem..."))
            subprocess.getoutput('mount --bind /var/run/dbus \"' + os.path.join(self.customDir, "root/var/run/dbus") + '\"')
	
            # copy apt.conf
            print(_("Copying apt.conf configuration..."))
            if not os.path.exists(os.path.join(self.customDir, "root/etc/apt/apt.conf.d")):
                os.makedirs(os.path.join(self.customDir, "root/etc/apt/apt.conf.d"))
            subprocess.getoutput('cp -f /etc/apt/apt.conf.d/* ' + os.path.join(self.customDir, "root/etc/apt/apt.conf.d"))
            # copy wgetrc
            print(_("Copying wgetrc configuration..."))
            # backup
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\"')
            subprocess.getoutput('cp -f /etc/wgetrc ' + os.path.join(self.customDir, "root/etc/wgetrc"))
            terminal = self.getTerminal()
            # run module script using COLORTERM if available -- more features
            if terminal != '' and subprocess.getoutput('which ' + terminal) != '':
                print(_('Launching Chroot ' + terminal + '...'))
                failed = subprocess.getoutput(terminal + '--hide-menubar -t \"Reconstructor Modules\" -x chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/module-exec.sh')
                if subprocess.getoutput('echo' + failed + ' | grep fail') != '':
                    print(_(failed + '\nLaunching Chroot Xterm...'))
                    subprocess.getoutput('xterm -bg black -fg white -rightbar -title \'Reconstructor Modules\' -e chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/module-exec.sh')
            else:
                print(_('Launching Chroot Xterm...'))
                # run module script using xterm if COLORTERM isn't available
                subprocess.getoutput('xterm -bg black -fg white -rightbar -title \'Reconstructor Modules\' -e chroot \"' + os.path.join(self.customDir, "root/") + '\" /tmp/module-exec.sh')
            # cleanup
            subprocess.getoutput('cd \"' + os.path.join(self.customDir, "root/tmp/") + '\"')
            subprocess.getoutput('rm -Rf *.rmod 1>&2 2>/dev/null')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/tmp/module-exec.sh") + '\" 1>&2 2>/dev/null')
            # restore wgetrc
            print(_("Restoring wgetrc configuration..."))
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\"')
            # remove apt.conf
            #print(_("Removing apt.conf configuration..."))
            #subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/apt/apt.conf.d/*") + '\"')
            # remove dns info
            print(_("Removing DNS info..."))
            subprocess.getoutput('rm -f \"' + os.path.join(self.customDir, "root/etc/resolv.conf") + '\"')
            subprocess.getoutput('ln -s /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))

            # umount /var/run/dbus
            print(_("Umounting -lf /var/run/dubs..."))
            error = subprocess.getoutput('umount  -lf \"' + os.path.join(self.customDir, "root/var/run/dbus/") + '\"')
            if(error != ''):
                self.suggestReboot('/var/run/dbus could not be unmounted. It must be unmounted before you can build an ISO.')
            # umount /proc
            print(_("Umounting /proc..."))
            error = subprocess.getoutput('umount  -lf \"' + os.path.join(self.customDir, "root/proc/") + '\"')
            if(error != ''):
                self.suggestReboot('/proc could not be unmounted. It must be unmounted before you can build an ISO.')

        # HACK: check for run on boot scripts and clear previous if new ones selected
        self.bootModulesEnabled = False;
        if self.treeModel != None:
            self.treeModel.foreach(self.checkBootModuleEnabled)
        if self.bootModulesEnabled == True:
            # create module script to add to live cd for modules that run on boot
            print(_('Copying modules that run on boot...'))
            modScrRunOnBoot = '#/bin/sh\n\nsleep 5\n'
            # clear previous
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/") + '\"')
            # copy all "run on boot" enabled scripts
            self.treeModel.foreach(self.copyRunOnBootModule)
            for bootModRoot, bootModDirs, bootModFiles in os.walk(os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/")):
                for bootMod in bootModFiles:
                    r, ext = os.path.splitext(bootMod)
                    if ext == '.rmod':
                        modScrRunOnBoot += '\necho Running Module: ' + os.path.basename(bootMod) + '\n'
                        modScrRunOnBoot += '\"/usr/share/reconstructor/scripts/' + os.path.basename(bootMod) + '\"' + ' ; '

            modScrRunOnBoot += '\nsudo rm -Rf /etc/skel/.gnomerc\nsudo rm -Rf /usr/share/reconstructor/\necho \'Modules Finished...\'\n\nsleep 5'
            # create boot mod script
            print(_('Generating boot module script...'))
            # remove existing
            if os.path.exists(os.path.join(self.customDir, "root/etc/skel/.gnomerc")):
                subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/skel/.gnomerc") + '\"')
            fGnomerc = open(os.path.join(self.customDir, "root/etc/skel/.gnomerc"), 'w')
            fGnomerc.write("bash /usr/share/reconstructor/scripts/boot-scripts-exec.sh &")
            fGnomerc.close()
            subprocess.getoutput('chmod -R 777 \"' + os.path.join(self.customDir, "root/etc/skel/.gnomerc") + '\"')
            fbootModScript = open(os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/boot-scripts-exec.sh"), 'w')
            fbootModScript.write(modScrRunOnBoot)
            fbootModScript.close()
            subprocess.getoutput('chmod a+x \"' + os.path.join(self.customDir, "root/usr/share/reconstructor/scripts/boot-scripts-exec.sh") + '\"')
            # chmod all scripts
            subprocess.getoutput('chmod -R 775 \"' + os.path.join(self.customDir, "root/usr/share/reconstructor/") + '\"')

        # manual software
        # check for manual install
        if self.manualInstall == True:
            print(_("Manually installing all existing .deb archives in /var/cache/apt/archives..."))
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' dpkg -i -R /var/cache/apt/archives/ 1>&2 2>/dev/null')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get clean')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get autoclean')

        # DEPRECATED - replacing with module framework
        # install software

        # install regular software
        if self.checkSoftware() == True:
            # add current user to the access control list
            user = subprocess.getoutput('echo $USER')
            print(_("Adding user " + user + " to access control list..."))
            subprocess.getoutput('xhost +local:' + user)
            # copy dns info
            if os.path.exists("/etc/resolv.conf"):
                print(_("Copying DNS info..."))
                subprocess.getoutput('cp -L --remove-destination /etc/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            elif os.path.exists("/run/resolvconf/resolv.conf"):
                print(_("Copying DNS info..."))
                subprocess.getoutput('cp -L --remove-destination /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))
            # mount /proc
            print(_("Mounting /proc filesystem..."))
            subprocess.getoutput('mount -t proc none \"' + os.path.join(self.customDir, "root/proc") + '\"')
            # copy apt.conf
            print(_("Copying apt.conf configuration..."))
            if not os.path.exists(os.path.join(self.customDir, "root/etc/apt/apt.conf.d/")):
                os.makedirs(os.path.join(self.customDir, "root/etc/apt/apt.conf.d/"))
            subprocess.getoutput('cp -f /etc/apt/apt.conf.d/* ' + os.path.join(self.customDir, "root/etc/apt/apt.conf.d/"))
            # copy wgetrc
            print(_("Copying wgetrc configuration..."))
            # backup
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\"')
            subprocess.getoutput('cp -f /etc/wgetrc ' + os.path.join(self.customDir, "root/etc/wgetrc"))
            # update ONLY if repositories are selected
            if self.checkCustomRepos() == True:
                print(_("Updating APT Information..."))
                # update apt
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get update ')
            # clean cache
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get clean')
            subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get autoclean')

            # custom apt-get
            if self.builder.get_object("entryCustomAptInstall").get_text() != "":
                print(_("Installing Custom Software..."))
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get install --assume-yes --force-yes -d ' + self.builder.get_object("entryCustomAptInstall").get_text())
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' dpkg -i -R /var/cache/apt/archives/ 1>&2 2>/dev/null')
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get clean')
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get autoclean')

            # custom software removal
            if self.builder.get_object("entryCustomAptRemove").get_text() != "":
                print(_("Removing Custom Software..."))
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' dpkg -P ' + self.builder.get_object("entryCustomAptRemove").get_text() + ' 1>&2 2>/dev/null')
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' dpkg --configure -a')
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get clean')
                subprocess.getoutput('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + ' apt-get autoclean')


            # restore wgetrc
            print(_("Restoring wgetrc configuration..."))
            subprocess.getoutput('mv -f \"' + os.path.join(self.customDir, "root/etc/wgetrc.orig") + '\" \"' + os.path.join(self.customDir, "root/etc/wgetrc") + '\"')
            # remove apt.conf
            #print(_("Removing apt.conf configuration..."))
            #subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "root/etc/apt/apt.conf") + '\"')
            # remove dns info
            print(_("Removing DNS info..."))
            subprocess.getoutput('rm -f \"' + os.path.join(self.customDir, "root/etc/resolv.conf") + '\"')
            subprocess.getoutput('ln -s /run/resolvconf/resolv.conf ' + os.path.join(self.customDir, "root/etc/resolv.conf"))

            # umount /proc
            print(_("Umounting /proc..."))
            error = subprocess.getoutput('umount  -lf \"' + os.path.join(self.customDir, "root/proc/") + '\"')
            if(error != ''):
                self.suggestReboot('/proc could not be unmounted. It must be unmounted before you can build an ISO.')
            self.setDefaultCursor()
            self.setPage(self.pageLiveBuild)




# ---------- Customize Alternate ----- #
    def customizeAlt(self):
        # get alternate cd info
        self.altCdUbuntuDist = 'unknown'
        self.altCdUbuntuVersion = 'unknown'
        self.altCdUbuntuArch = 'unknown'
        # build regex for info
        r = re.compile(self.regexUbuntuAltCdInfo, re.IGNORECASE)
        f = open(os.path.join(self.customDir, "remaster_alt/.disk/info"), 'r')
        for l in f:
            if r.match(l) != None:
                self.altCdUbuntuDist = r.match(l).group(1)
                self.altCdUbuntuVersion = r.match(l).group(2)
                self.altCdUbuntuArch = r.match(l).group(3)
        f.close()
        distText = _('Distribution:')
        verText = _('Version:')
        archText = _('Architecture:')
        print(distText + ' ' + self.altCdUbuntuDist)
        print(verText + ' ' + self.altCdUbuntuVersion)
        print(archText + ' ' + self.altCdUbuntuArch)

        # load ubuntu codename for apt
        self.ubuntuCodename = ''
        if self.altCdUbuntuVersion == self.dapperVersion:
            self.ubuntuCodename = 'dapper'
        elif self.altCdUbuntuVersion == self.edgyVersion:
            self.ubuntuCodename = 'edgy'
        elif self.altCdUbuntuVersion == self.feistyVersion:
            self.ubuntuCodename = 'feisty'
        elif self.altCdUbuntuVersion == self.gutsyVersion:
            self.ubuntuCodename = 'gutsy'
        elif self.altCdUbuntuVersion == self.hardyVersion:
            self.ubuntuCodename = 'hardy'
        elif self.altCdUbuntuVersion == self.intrepidVersion:
            self.ubuntuCodename = 'intrepid'
        elif self.altCdUbuntuVersion == self.jauntyVersion:
            self.ubuntuCodename = 'jaunty'
        elif self.altCdUbuntuVersion == self.karmicVersion:
            self.ubuntuCodename = 'karmic'
        else:
            print(_("Unable to detect codename for Ubuntu CD Version - APT Repositories will NOT be modified..."))


        # set up apt repos
        if self.checkAltCustomRepos() == True:
            # move old sources.list apt file
            print(_("Backing up old apt config..."))
            subprocess.getoutput('mv -f /etc/apt/sources.list /etc/apt/sources.list.orig')
            subprocess.getoutput('cp -Rf /var/cache/apt /var/cache/apt.orig')
            # check for directories and create if necessary
            if os.path.exists(os.path.join(self.customDir, self.altRemasterRepo)) == False:
                subprocess.getoutput('mkdir -p \"' + os.path.join(self.customDir, self.altRemasterRepo) + '\"')
            if os.path.exists(os.path.join(self.customDir, self.altRemasterRepo + "/archives")) == False:
                subprocess.getoutput('mkdir -p \"' + os.path.join(self.customDir, self.altRemasterRepo + "/archives/partial") + '\"')
            subprocess.getoutput('chmod -R 775 \"' + os.path.join(self.customDir, self.altRemasterRepo) + '\"')

            if self.ubuntuCodename != '':
                # ubuntu official
                if self.builder.get_object("checkbuttonAltUbuntuOfficialRepo").get_active() == True:
                    print(_("Adding Ubuntu Official Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + self.ubuntuCodename + ' main\" >> /etc/apt/sources.list')
                    print(_('Adding Ubuntu Official Security Repository...'))
                    subprocess.getoutput('echo \"deb http://security.ubuntu.com/ubuntu ' + self.ubuntuCodename +'-security main restricted\" >> /etc/apt/sources.list')
                    subprocess.getoutput('echo \"deb-src http://security.ubuntu.com/ubuntu ' + self.ubuntuCodename + '-security main restricted\" >> /etc/apt/sources.list')

                # ubuntu restricted
                if self.builder.get_object("checkbuttonAltUbuntuRestrictedRepo").get_active() == True:
                    print(_("Adding Ubuntu Restricted Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + self.ubuntuCodename + ' restricted\" >> /etc/apt/sources.list')

                # ubuntu universe
                if self.builder.get_object("checkbuttonAltUbuntuUniverseRepo").get_active() == True:
                    print(_("Adding Ubuntu Universe Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + self.ubuntuCodename + ' universe\" >> /etc/apt/sources.list')
                    print(_('Adding Ubuntu Universe Security Repository...'))
                    subprocess.getoutput('echo \"deb http://security.ubuntu.com/ubuntu ' + self.ubuntuCodename + '-security universe\" >> /etc/apt/sources.list')
                    subprocess.getoutput('echo \"deb-src http://security.ubuntu.com/ubuntu ' + self.ubuntuCodename + '-security universe\" >> /etc/apt/sources.list')

                # ubuntu multiverse
                if self.builder.get_object("checkbuttonAltUbuntuMultiverseRepo").get_active() == True:
                    print(_("Adding Ubuntu Multiverse Apt Repository..."))
                    subprocess.getoutput('echo \"deb http://archive.ubuntu.com/ubuntu/ ' + self.ubuntuCodename + ' multiverse\" >> /etc/apt/sources.list')

                # ubuntu official updates
                print(_("Adding Ubuntu Official Updates Apt Repository..."))
                subprocess.getoutput('echo \"deb http://us.archive.ubuntu.com/ubuntu/ ' + self.ubuntuCodename + '-updates main restricted\" >> /etc/apt/sources.list')

                # custom archives
                buf = self.builder.get_object("textviewAltAptCustomRepos").get_buffer()
                if buf.get_text(buf.get_start_iter(),buf.get_end_iter()) != '':
                    print(_("Adding Custom Apt Repositories..."))
                    subprocess.getoutput('echo \"' + buf.get_text(buf.get_start_iter(),buf.get_end_iter()) + '\" >> /etc/apt/sources.list.d/reconstructor.list')

                # download packages
                buf = self.builder.get_object("textviewAltPackages").get_buffer()
                if buf.get_text(buf.get_start_iter(),buf.get_end_iter()) != '':
                    print(_("Updating apt (apt-get update)..."))
                    subprocess.getoutput('apt-get update')
                    print(_("Downloading extra packages..."))
                    print(subprocess.getoutput('apt-get install -d -y -m --reinstall --allow-unauthenticated -o Dir::Cache=\"' + os.path.join(self.customDir, self.altRemasterRepo) + '/\" ' + buf.get_text(buf.get_start_iter(),buf.get_end_iter())))


                # copy .debs to remaster dir
                # check for extras dir
                if os.path.exists(os.path.join(self.customDir, self.altRemasterDir) + "/dists/" + self.ubuntuCodename + "/extras") == False:
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
                    subprocess.getoutput('mkdir -p dists/' + self.ubuntuCodename + '/extras/binary-' + self.altCdUbuntuArch)
                # pool dir
                if os.path.exists(os.path.join(self.customDir, self.altRemasterDir) + "/pool/extras") == False:
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
                    subprocess.getoutput('mkdir -p pool/extras')
                # check and copy
                if subprocess.getoutput('ls \"' + os.path.join(self.customDir, self.altRemasterRepo) + '/archives\"' + ' | grep .deb') != '':
                    print(_("Copying downloaded archives into pool..."))
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterRepo) + '/archives\"')
                    subprocess.getoutput('cp -R *.deb \"' + os.path.join(self.customDir, self.altRemasterDir) + '/pool/extras/\"')
                    #print(_("Cleaning temporary apt cache..."))
                    subprocess.getoutput('apt-get clean -o Dir::Cache=\"' + os.path.join(self.customDir, self.altRemasterRepo) + '/\" ')

                # check dependencies for extras
                p = PackageHelper(customDirectory=self.customDir, remasterDirectory=self.altRemasterDir, remasterRepoDirectory=self.altRemasterRepo, remasterTempDirectory=self.tmpDir, distribution=self.ubuntuCodename)
                print(_("Checking and downloading dependencies for extra packages..."))
                p.resolveDependencies()

                #print(_("Cleaning temporary apt cache..."))
                subprocess.getoutput('apt-get clean -o Dir::Cache=\"' + os.path.join(self.customDir, self.altRemasterRepo) + '/\" ')

                print(_("Restoring original apt configuration..."))
                subprocess.getoutput('mv -f /etc/apt/sources.list.orig /etc/apt/sources.list')
                subprocess.getoutput('rm -Rf /var/cache/apt')
                subprocess.getoutput('mv -f /var/cache/apt.orig /var/cache/apt')
                subprocess.getoutput('rm -Rf /var/cache/apt.orig')


        # check for pool dir
        if os.path.exists(os.path.join(self.customDir, self.altRemasterDir) + '/pool/extras' ) == True:
            # check for debs
            if subprocess.getoutput('ls \"' + os.path.join(self.customDir, self.altRemasterDir) + '/pool/extras/\"' + ' | grep .deb') != '':
                # create Release file
                print(_("Creating Release file..."))
                # check for extras directory
                if os.path.exists(os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/extras/binary-' + self.altCdUbuntuArch) == False:
                    subprocess.getoutput('mkdir -p \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/extras/binary-' + self.altCdUbuntuArch + '\"')
                f=open(os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/extras/binary-' + self.altCdUbuntuArch + '/Release', 'w')
                f.write('Archive: ' + self.ubuntuCodename + '\nVersion: ' + self.altCdUbuntuVersion + '\nComponent: extras\nOrigin: Ubuntu\nLabel: Ubuntu\nArchitecture: ' + self.altCdUbuntuArch + '\n')
                f.close()
                # check for GPG key and create if necessary
                status, output = commands.getstatusoutput('gpg --list-keys | grep \"' + self.altGpgKeyName +'\" > /dev/null')
                if status == 0:
                    # key found
                    print("GPG Key Found...")
                else:
                    # not found; create
                    print(_("No GPG Key found... Creating..."))
                    try:
                        # get key information
                        gpgKeyEmail, gpgKeyPhrase = None, None
                        try:
                            gpgKeyEmail, gpgKeyPhrase = self.getGpgKeyInfo()
                        except:
                            pass
                        if gpgKeyEmail != None and gpgKeyPhrase != None:
                            #print(gpgKeyEmail, gpgKeyPhrase)
                            # create key
                            key = "Key-Type: DSA\nKey-Length: 1024\nSubkey-Type: ELG-E\nSubkey-Length: 2048\nName-Real: " + self.altGpgKeyName + "\nName-Comment: " + self.altGpgKeyComment + "\nName-Email: " + gpgKeyEmail + "\nExpire-Date: 0\nPassphrase: " + gpgKeyPhrase
                            #print(key)
                            f = open(os.path.join(self.customDir, self.tmpDir) + '/gpg.key', 'w')
                            f.write(key)
                            f.close()
                            # create the key from the gpg.key file
                            subprocess.getoutput('gpg --gen-key --batch --gen-key \"' + os.path.join(self.customDir, self.tmpDir) + '/gpg.key\" > /dev/null')
                            # reset permissions for user
                            subprocess.getoutput('chown -R ' + os.getlogin() + ' \"' + os.environ['HOME'] + '/.gnupg/\"')
                            print(_("GPG Key Generation Finished..."))
                            # remove key generation file
                            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, self.tmpDir) + '/gpg.key\"')

                        else:
                            raise(Exception, _("Email and passphrase must not be empty and must match..."))
                            self.setDefaultCursor()
                            return False
                    except Exception as detail:
                        errText = _("Error Creating GPG Key:")
                        print(errText, detail)
                        self.setDefaultCursor()
                        return False

                # create apt.conf
                if os.path.exists(os.path.join(self.customDir, self.tmpDir) + '/apt.conf.d/99reconstructor') == False:
                    print(_("Creating apt.conf..."))
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
                    subprocess.getoutput('cat dists/' + self.ubuntuCodename + '/Release | egrep -v \"^ \" | egrep -v \"^(Date|MD5Sum|SHA1)\" | sed \'s/: / \"/\' | sed \'s/^/APT::FTPArchive::Release::/\' | sed \'s/$/\";/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt.conf.d/99reconstructor\"')

                # build paths for conf files (so sed can understand them...)
                archDir = os.path.join(self.customDir, self.altRemasterDir)
                archDir = archDir.replace('/', '\\/')
                indexDir = os.path.join(self.customDir, self.tmpDir)
                indexDir = indexDir.replace('/', '\\/')
                #check for apt-ftparchive-deb.conf
                if os.path.exists(os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf') == False:
                    # create apt-ftparchive-deb.conf
                    print(_("Creating apt-ftparchive-deb.conf..."))
                    # add archive dir path
                    subprocess.getoutput('cat \"' + cur_file_dir + '/lib/apt-ftparchive-deb.conf\" | sed \'s/ARCHIVEDIR/' + archDir + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf\"')
                    # add dist
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf\" | sed \'s/DIST/' + self.ubuntuCodename + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-deb.conf.tmp apt-ftparchive-deb.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-deb.conf.tmp')
                    # add architecture
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf\" | sed \'s/ARCH/' + self.altCdUbuntuArch + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-deb.conf.tmp apt-ftparchive-deb.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-deb.conf.tmp')
                    # add index path
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf\" | sed \'s/INDEXDIR/' + indexDir + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-deb.conf.tmp apt-ftparchive-deb.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-deb.conf.tmp')

                # check for apt-ftparchive-udeb.conf
                if os.path.exists(os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf') == False:
                    print(_("Creating apt-ftparchive-udeb.conf..."))
                    # add archive dir path
                    subprocess.getoutput('cat \"' + cur_file_dir + '/lib/apt-ftparchive-udeb.conf\" | sed \'s/ARCHIVEDIR/' + archDir + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf\"')
                    # add dist
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf\" | sed \'s/DIST/' + self.ubuntuCodename + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-udeb.conf.tmp apt-ftparchive-udeb.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-udeb.conf.tmp')
                    # add architecture
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf\" | sed \'s/ARCH/' + self.altCdUbuntuArch + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-udeb.conf.tmp apt-ftparchive-udeb.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-udeb.conf.tmp')
                    # add index path
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf\" | sed \'s/INDEXDIR/' + indexDir + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-udeb.conf.tmp apt-ftparchive-udeb.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-udeb.conf.tmp')

                # check for apt-ftparchive-extras.conf
                if os.path.exists(os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-extras.conf') == False:
                    print(_("Creating apt-ftparchive-extras.conf..."))
                    # add archive dir path
                    subprocess.getoutput('cat \"' + cur_file_dir + '/lib/apt-ftparchive-extras.conf\" | sed \'s/ARCHIVEDIR/' + archDir + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-extras.conf\"')
                    # add dist
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-extras.conf\" | sed \'s/DIST/' + self.ubuntuCodename + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-extras.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-extras.conf.tmp apt-ftparchive-extras.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-extras.conf.tmp')
                    # add architecture
                    subprocess.getoutput('cat \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-extras.conf\" | sed \'s/ARCH/' + self.altCdUbuntuArch + '/\' > \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-extras.conf.tmp\"')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('mv apt-ftparchive-extras.conf.tmp apt-ftparchive-extras.conf')
                    subprocess.getoutput('rm -f apt-ftparchive-extras.conf.tmp')

                print(_("Checking Indices..."))
                if os.path.exists (os.path.join(self.customDir, self.tmpDir) + '/override.' + self.ubuntuCodename + '.main') == False:
                    print("Getting index: override." + self.ubuntuCodename + ".main ...")
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('wget -nv http://archive.ubuntu.com/ubuntu/indices/override.' + self.ubuntuCodename + '.main')
                if os.path.exists (os.path.join(self.customDir, self.tmpDir) + '/override.' + self.ubuntuCodename + '.extra.main') == False:
                    print("Getting index: override." + self.ubuntuCodename + ".extra.main ...")
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('wget -nv http://archive.ubuntu.com/ubuntu/indices/override.' + self.ubuntuCodename + '.extra.main')
                if os.path.exists (os.path.join(self.customDir, self.tmpDir) + '/override.' + self.ubuntuCodename + '.main.debian-installer') == False:
                    print("Getting index: override." + self.ubuntuCodename + ".main.debian-installer ...")
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('wget -nv http://archive.ubuntu.com/ubuntu/indices/override.' + self.ubuntuCodename + '.main.debian-installer')

                # check for extra2.main override
                if os.path.exists(os.path.join(self.customDir, self.tmpDir) + '/override.' + self.ubuntuCodename + '.extra2.main') == False:
                    # create a 'fixed' version of extra.main override
                    print("Fixing index: override." + self.ubuntuCodename + ".extra.main ...")
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                    subprocess.getoutput('cat override.'+ self.ubuntuCodename + '.extra.main | egrep -v \' Task \' > override.' + self.ubuntuCodename + '.extra2.main')
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
                    subprocess.getoutput('cat dists/' + self.ubuntuCodename + '/main/binary-' + self.altCdUbuntuArch + '/Packages | perl -e \'while (<>) { chomp; if(/^Package\:\s*(.+)$/) { $pkg=$1; } elsif(/^Task\:\s(.+)$/) { print(\"$pkg\tTask\t$1\n\"); } }\' >> ' + os.path.join(self.customDir, self.tmpDir) + '/override.' + self.ubuntuCodename + '.extra2.main')

                # download ubuntu keyring
                # move old sources.list apt file
                print(_("Backing up old apt config..."))
                subprocess.getoutput('mv -f /etc/apt/sources.list /etc/apt/sources.list.orig')
                subprocess.getoutput('cp -Rf /var/cache/apt /var/cache/apt.orig')

                # remove old ubuntu-keyring
                print(_("Removing existing ubuntu-keyring source..."))
                subprocess.getoutput('rm -Rf ' + os.path.join(self.customDir, self.tmpDir) + '/ubuntu-keyring*')

                # add deb-src to apt sources
                subprocess.getoutput('echo deb-src http://us.archive.ubuntu.com/ubuntu ' + self.ubuntuCodename + ' main restricted > /etc/apt/sources.list')
                print(_("Updating apt (apt-get update)..."))
                subprocess.getoutput('apt-get update')
                # download ubuntu-keyring for keyring generation
                print(_("Getting Ubuntu Keyring source..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                subprocess.getoutput('apt-get source ubuntu-keyring')

                print(_("Restoring original apt configuration..."))
                subprocess.getoutput('mv -f /etc/apt/sources.list.orig /etc/apt/sources.list')
                subprocess.getoutput('rm -Rf /var/cache/apt')
                subprocess.getoutput('mv -f /var/cache/apt.orig /var/cache/apt')
                subprocess.getoutput('rm -Rf /var/cache/apt.orig')
                # update local system apt so user doesn't have to later
                subprocess.getoutput('apt-get update')

                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                keyringDir = subprocess.getoutput('find * -maxdepth 1 -name "ubuntu-keyring*" -type d -print')
                # import ubuntu keyring
                print(_("Importing Ubuntu Key..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '/' + keyringDir + '/keyrings\" ')
                subprocess.getoutput('gpg --import < ubuntu-archive-keyring.gpg > /dev/null')
                subprocess.getoutput('rm -Rf ubuntu-archive-keyring.gpg > /dev/null')
                # reset permissions for user
                subprocess.getoutput('chown -R ' + os.getlogin() + ' \"' + os.environ['HOME'] + '/.gnupg/\"')
                print(_("Exporting new key..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '/' + keyringDir + '/keyrings\"')
                subprocess.getoutput('gpg --output=ubuntu-archive-keyring.gpg --export \"Ubuntu CD Image Automatic Signing Key\" \"Ubuntu Archive Automatic Signing Key\" \"' + self.altGpgKeyName + '\" > /dev/null' )
                print(_("Building new key package..."))
                # TODO: somehow pass the gpg passphrase so it doesn't prompt...
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '/' + keyringDir + '\"')
                subprocess.getoutput('dpkg-buildpackage -rfakeroot -m\"' + self.altGpgKeyName + '\" -k\"' + self.altGpgKeyName + '\" > /dev/null')
                # remove old ubuntu-keyring package
                print(_("Removing old ubuntu keyring package..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
                subprocess.getoutput('rm -Rf pool/main/u/ubuntu-keyring/*')
                # copy new keyring package
                print(_("Copying new ubuntu keyring package..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.tmpDir) + '\"')
                subprocess.getoutput('cp -Rf ubuntu-keyring*deb \"' + os.path.join(self.customDir, self.altRemasterDir) + '/pool/main/u/ubuntu-keyring/\"')

                # create apt package list
                print(_("Generating package lists..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
                print("  deb...")
                subprocess.getoutput('apt-ftparchive -c \"' + os.path.join(self.customDir, self.tmpDir) + '/apt.conf.d/99reconstructor\" generate \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-deb.conf\"')
                print("  udeb...")
                subprocess.getoutput('apt-ftparchive -c \"' + os.path.join(self.customDir, self.tmpDir) + '/apt.conf.d/99reconstructor\" generate \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-udeb.conf\"')
                subprocess.getoutput('cat dists/' + self.ubuntuCodename + '/main/binary-' + self.altCdUbuntuArch + '/Release | sed \'s/Component: main/Component: extras/\' > dists/' + self.ubuntuCodename + '/extras/binary-' + self.altCdUbuntuArch + '/Release')
                print("  extras...")
                subprocess.getoutput('apt-ftparchive -c \"' + os.path.join(self.customDir, self.tmpDir) + '/apt.conf.d/99reconstructor\" generate \"' + os.path.join(self.customDir, self.tmpDir) + '/apt-ftparchive-extras.conf\"')

                # remove existing release file
                print(_("Removing current Release file..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '\"')
                subprocess.getoutput('rm -Rf Release*')
                print(_("Generating new Release file..."))
                subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '\"')
                subprocess.getoutput('apt-ftparchive -c \"' + os.path.join(self.customDir, self.tmpDir) + '/apt.conf.d/99reconstructor\" release dists/' + self.ubuntuCodename + '/ > \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/Release\"')
                print(_("GPG signing new Release file..."))
                #subprocess.getoutput('echo \"' + self.altGpgKeyPhrase + '\" | gpg --default-key \"' + self.altGpgKeyName + '\" --passphrase-fd 0 --output \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/Release.gpg\" -ba \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/Release\"')
                subprocess.getoutput('gpg --default-key \"' + self.altGpgKeyName + '\" --output \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/Release.gpg\" -ba \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/Release\"')

                # build list for preseed
                # build regex
                r = re.compile(self.regexUbuntuAltPackages, re.IGNORECASE)
                # package list
                pkgs = ''
                fp = open(os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.ubuntuCodename + '/extras/binary-' + self.altCdUbuntuArch + '/Packages', 'r')
                for l in fp:
                    if r.match(l) != None:
                        pkgs += r.match(l).group(1) + ' '
                fp.close()

                # find distribution, correct preseed file (for isolinux.cfg), and write preseed
                preseedMain = ''
                seedfile = ''
                if self.altCdUbuntuDist == 'Ubuntu':
                    print(_("Creating preseed for Ubuntu..."))
                    preseedMain = 'tasksel    tasksel/first    multiselect ubuntu-desktop\n'
                    seedfile = 'ubuntu.seed'
                elif self.altCdUbuntuDist == 'Kubuntu':
                    print(_("Creating preseed for Kubuntu..."))
                    preseedMain = 'tasksel    tasksel/first    multiselect kubuntu-desktop\n'
                    seedfile = 'kubuntu.seed'
                elif self.altCdUbuntuDist == 'Xubuntu':
                    print(_("Creating preseed for Xubuntu..."))
                    preseedMain = 'tasksel    tasksel/first    multiselect xubuntu-desktop\n'
                    seedfile = 'xubuntu.seed'
                elif self.altCdUbuntuDist == 'Ubuntu-Server':
                    print(_("Creating preseed for Ubuntu-Server..."))
                    preseedMain = 'd-i    base-installer/kernel/override-image    string linux-server\nd-i    pkgsel/language-pack-patterns    string\nd-i    pkgsel/install-language-support    boolean false\n'
                    seedfile = 'ubuntu-server.seed'
                else:
                    print(_("Error: Unknown distribution. Skipping preseed creation..."))
                # write preseed
                if preseedMain != '':
                    if os.path.exists(os.path.join(self.customDir, self.altRemasterDir) + '/preseed/custom.seed'):
                        # remove preseed
                        subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, self.altRemasterDir) + '/preseed/custom.seed\"')
                    fs = open(os.path.join(self.customDir, self.altRemasterDir) + '/preseed/custom.seed', 'w')
                    preseedMain += 'd-i pkgsel/include string ' + pkgs
                    fs.write(preseedMain)
                    fs.close
                # write custom isolinux.cfg
                if seedfile != '':
                    print(_("Creating isolinux.cfg..."))
                    subprocess.getoutput('cd \"' + os.path.join(self.customDir, self.altRemasterDir) + '/isolinux/\"')
                    subprocess.getoutput('cat isolinux.cfg | sed \'s/' + seedfile + '/custom.seed/\' > isolinux.cfg.tmp ; mv isolinux.cfg.tmp isolinux.cfg')

        # no packages
        else:
            # no extra packages found
            print(_("No extra packages found..."))

        self.setDefaultCursor()
        print(_("Finished customizing alternate install..."))
        print(" ")
        # calculate iso size in the background
        self.run_generator(self.calculateAltIsoSize)
        #return False

# ---------- Build ---------- #
    def build(self):
        self.setBusyCursor()
        # check for custom mksquashfs (for multi-threading, new features, etc.)
        mksquashfs = ''
        if subprocess.getoutput('echo $MKSQUASHFS') != '':
            mksquashfs = subprocess.getoutput('echo $MKSQUASHFS')
            print('Using alternative mksquashfs: ' + ' Version: ' + subprocess.getoutput(mksquashfs + ' -version'))
        # setup build vars
        self.buildInitrd = self.builder.get_object("checkbuttonBuildInitrd").get_active()
        self.buildSquashRoot = self.builder.get_object("checkbuttonBuildSquashRoot").get_active()
        self.buildIso = self.builder.get_object("checkbuttonBuildIso").get_active()
        self.buildLiveCdFilename = self.builder.get_object("entryLiveIsoFilename").get_text()
        self.LiveCdDescription = "ubuntu-custom"
        self.LiveCdRemovePrograms = self.builder.get_object("checkbuttonLiveCdRemoveWin32Programs").get_active()
        self.LiveCdArch = self.builder.get_object("comboboxLiveCdArch").get_active_text()
        self.hfsMap = cur_file_dir + "/lib/hfs.map"

        print(" ")
        print(_("INFO: Starting Build..."))
        print(" ")
        self.showProgress('Starting Build...',0.56)
        yield True
        # build initrd
        if self.buildInitrd == True:
            # create initrd
            kver = find_newest_kernel_version(os.path.join(self.customDir, "root/lib/modules"))
            if kver != '' and os.path.exists(os.path.join(self.customDir, "initrd")):
                print(_("Creating Initrd..."))
                self.showProgress(_("Creating Initrd..."))
                yield True
                self.liveCDKernel()
            self.showProgress(False,0.65)
            yield True

        # build squash root
        if self.buildSquashRoot == True:
            # create squashfs root
            if os.path.exists(os.path.join(self.customDir, "root")):
                print(_("Creating SquashFS root..."))
                self.showProgress(_("Creating SquashFS root..."),0.66)
                yield True
                print(_("Updating File lists..."))
                q = ' dpkg-query -W --showformat=\'${Package} ${Version}\n\' '
                subprocess.check_output('chroot \"' + os.path.join(self.customDir, "root/") + '\"' + q + ' > \"' + os.path.join(self.customDir, "remaster/casper/filesystem.manifest") + '\"', shell=True )
                subprocess.getoutput('cp -f \"' + os.path.join(self.customDir, "remaster/casper/filesystem.manifest") + '\" \"' + os.path.join(self.customDir, "remaster/casper/filesystem.manifest-desktop") + '\"')

                # check for existing squashfs root
                if os.path.exists(os.path.join(self.customDir, "remaster/casper/filesystem.squashfs")):
                    print(_("Removing existing SquashFS root..."))
                    subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/casper/filesystem.squashfs") + '\"')

                # remove aptitude lock and crash logs
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/var/lib/apt/lists/lock"))
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/var/crash/*"))

                # remove some history files
                print(_("Cleaning bash history..."))
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/root/.bash_histroy"))
                
                # remove kernel file
                kernelVmlinuz = subprocess.getoutput("readlink " + os.path.join(self.customDir,"root/vmlinuz"))
                kernelInitrd = subprocess.getoutput("readlink " + os.path.join(self.customDir,"root/initrd.img"))
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir,"root/" + kernelVmlinuz))
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir,"root/" + kernelInitrd)) 

                print(_("Building SquashFS root..."))
                self.showProgress(_("Building SquashFS root..."),0.70)
                yield True
                # check for alternate mksquashfs
                self.setBusyCursor()
                compStr=''
                if apt_pkg.version_compare(self.cdUbuntuVersion,'10.04')>0:
                        compStr="-comp xz"
                if mksquashfs == '':
                    subprocess.getoutput(self.timeCmd + ' mksquashfs \"' + os.path.join(self.customDir, "root/") + '\"' + ' \"' + os.path.join(self.customDir, "remaster/casper/filesystem.squashfs") + '\" ' + compStr)
                else:
                    subprocess.getoutput(self.timeCmd + ' ' + mksquashfs + ' \"' + os.path.join(self.customDir, "root/") + '\"' + ' \"' + os.path.join(self.customDir, "remaster/casper/filesystem.squashfs") + '\" '+ compStr)
                self.showProgress(_("Finished Building SquashFS root"),0.85)
                yield True

        # remove windows programs
        if self.LiveCdRemovePrograms == True:
            print(_('Removing Win32 versions of Firefox, Thunderbird, etc. ...'))
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/bin") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/programs") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/autorun.inf") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/start.ini") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/start.exe") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/start.bmp") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/umenu.exe") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/wubi.exe") + '\"')
            subprocess.getoutput('rm -Rf \"' + os.path.join(self.customDir, "remaster/wubi-cdboot.exe") + '\"')
            self.showProgress(False,0.87)
            yield True

        # build iso
        if self.buildIso == True:
            # create iso
            if os.path.exists(os.path.join(self.customDir, "remaster")):
                print(_("Creating ISO..."))
                self.showProgress(_("Creating ISO..."),0.87)
                yield True
                self.setBusyCursor()
                # add disc id
                subprocess.getoutput('echo \"Built by Reconstructor ' + self.appVersion + ' - Rev ' + self.updateId + ' (c) Reconstructor Team, 2006-2009 - http://reconstructor.aperantis.com\" > \"' + os.path.join(self.customDir, "remaster/.disc_id") + '\"')
                # update md5
                print(_("Updating md5 sums..."))
                subprocess.getoutput('rm \"' + os.path.join(self.customDir, "remaster/") + 'md5sum.txt\"')
                # exclude isolinux directory or else when checking disc integrity it will say there are errors
                subprocess.getoutput('(cd \"' + os.path.join(self.customDir, "remaster/") + '\"')
                subprocess.getoutput('find . -type f -not -name md5sum.txt -not -path \'*/isolinux/*\' -print0 | xargs -0 md5sum > md5sum.txt)')
                rootSize = self.FileSize(os.path.join(self.customDir, "root/"))
                print('%lu'%(rootSize), file=open(os.path.join(self.customDir, "remaster/casper/filesystem.size"),"w"))
                self.showProgress(False,0.88)
                yield True

                # remove existing iso
                if os.path.exists(self.buildLiveCdFilename):
                    print(_("Removing existing ISO..."))
                    subprocess.getoutput('rm -Rf \"' + self.buildLiveCdFilename + '\"')
                    self.showProgress(False,0.89)
                    yield True
                # build
                # check for description - replace if necessary
                if self.builder.get_object("entryLiveCdDescription").get_text() != "":
                    self.LiveCdDescription = self.builder.get_object("entryLiveCdDescription").get_text()

                self.showProgress(False,0.90)
                yield True

                self.setBusyCursor()
                # build iso according to architecture
                if self.LiveCdArch == "x86":
                    print(_("Building x86 ISO..."))
                    subprocess.getoutput(self.timeCmd + ' mkisofs -o \"' + self.buildLiveCdFilename + '\" -b \"isolinux/isolinux.bin\" -c \"isolinux/boot.cat\" -no-emul-boot -boot-load-size 4 -boot-info-table -V \"' + self.LiveCdDescription + '\" -cache-inodes -r -J -l \"' + os.path.join(self.customDir, "remaster") + '\"')
                elif self.LiveCdArch == "PowerPC":
                    print(_("Building PowerPC ISO..."))
                    subprocess.getoutput(self.timeCmd + ' mkisofs  -r -V \"' + self.LiveCdDescription + '\" --netatalk -hfs -probe -map \"' + self.hfsMap + '\" -chrp-boot -iso-level 2 -part -no-desktop -hfs-bless ' + '\"' + os.path.join(self.customDir, "remaster/install") + '\" -o \"' + self.buildLiveCdFilename + '\" \"' + os.path.join(self.customDir, "remaster") + '\"')
                elif self.LiveCdArch == "x86_64":
                    print(_("Building x86_64 ISO..."))
                    subprocess.getoutput(self.timeCmd + ' mkisofs -o \"' + self.buildLiveCdFilename + '\" -b \"isolinux/isolinux.bin\" -c \"isolinux/boot.cat\" -no-emul-boot -boot-load-size 4 -boot-info-table -V \"' + self.LiveCdDescription + '\" -cache-inodes -r -J -l \"' + os.path.join(self.customDir, "remaster") + '\"')
                self.showProgress(False,0.98)
                yield True

        self.setDefaultCursor()
        self.setPage(self.pageFinish)
        # print(status message)
        statusMsgFinish = _('     <b>Finished.</b>     ')
        statusMsgISO = _('      <b>Finished.</b> ISO located at: ')
        if os.path.exists(self.buildLiveCdFilename):
            print("ISO Located: " + self.buildLiveCdFilename)
            self.builder.get_object("labelBuildComplete").set_text(statusMsgISO + self.buildLiveCdFilename + '     ')
            self.builder.get_object("labelBuildComplete").set_use_markup(True)
        else:
            self.builder.get_object("labelBuildComplete").set_text(statusMsgFinish)
            self.builder.get_object("labelBuildComplete").set_use_markup(True)
        # enable/disable iso burn
        self.checkEnableBurnIso()

        print("Build Complete...")
        self.showProgress('Build Complete.',1)
        yield False

#---------- Build alternate disc ----------#
    def buildAlternate(self):
        # setup build vars
        self.buildAltInitrd = self.builder.get_object("checkbuttonAltBuildInitrd").get_active()
        self.buildAltIso = self.builder.get_object("checkbuttonAltBuildIso").get_active()
        self.buildAltCdFilename = self.builder.get_object("entryAltBuildIsoFilename").get_text()
        self.altCdDescription = "ubuntu-custom-alt"
        self.altCdArch = self.builder.get_object("comboboxAltBuildArch").get_active_text()
        self.hfsMap = cur_file_dir + "/lib/hfs.map"

        print(" ")
        print(_("INFO: Starting Build..."))
        print(" ")
        # build initrd
        if self.buildAltInitrd == True:
            # create initrd
            kver=find_newest_kernel_version(os.path.join(self.customDir, "root/lib/modules"))
            if kver != '' and os.path.exists(os.path.join(self.customDir, "initrd_alt")):
                print(_("Creating Initrd..."))
                self.showProgress(_("Creating Initrd..."),0.75)
                yield True
                self.setBusyCursor()
                if os.path.exists(os.path.join(self.customDir, "remaster/casper/initrd.lz")):
                    scr = '#!/bin/sh\n#\n  cat /usr/sbin/mkinitramfs | sed -e \"s/gzip/lzma/g\" >/tmp/mkinitramfs-lzma ;chmod +x /tmp/mkinitramfs-lzma;cd /boot; /tmp/mkinitramfs-lzma -o initrd.img-'+kver+' '+kver+';rm -f /tmp/mkinitramfs-lzma\n'
                else:
                    scr = '#!/bin/sh\n#\n cd /boot; /usr/sbin/mkinitramfs -o initrd.img-'+kver+' '+kver+'\n'
                f=open(os.path.join(self.customDir, "root/tmp/lmkinitrafs.sh"), 'w')
                f.write(scr)
                f.close()
                subprocess.getoutput('chmod a+x ' + os.path.join(self.customDir, "root/tmp/lmkinitrafs.sh"))
                subprocess.getoutput('chroot \"'+os.path.join(self.customDir, "root/")+'\" /tmp/lmkinitrafs.sh >/dev/null 2>&1')
                subprocess.getoutput('rm -f ' + os.path.join(self.customDir, "root/tmp/lmkinitrafs.sh"))
                if os.path.exists(os.path.join(self.customDir, "remaster/casper/initrd.lz")):
                    subprocess.getoutput('cp '+os.path.join(self.customDir, "root/boot/initrd.img-"+kver+' ')+os.path.join(self.customDir, "remaster/casper/initrd.lz"))		
                else:
                    subprocess.getoutput('cp '+os.path.join(self.customDir, "root/boot/initrd.img-"+kver+' ')+os.path.join(self.customDir, "remaster/casper/initrd"))		
                if os.path.exists(os.path.join(self.customDir, "remaster/casper/vmlinuz.efi")):
                    subprocess.getoutput('cp '+os.path.join(self.customDir, "root/boot/vmlinuz-"+kver+' ')+os.path.join(self.customDir, "remaster/casper/vmlinuz.efi"))
                else:
                    subprocess.getoutput('cp '+os.path.join(self.customDir, "root/boot/vmlinuz-"+kver+' ')+os.path.join(self.customDir, "remaster/casper/vmlinuz"))
		
        # build iso
        if self.buildAltIso == True:
            # create iso
            if os.path.exists(os.path.join(self.customDir, "remaster_alt")):
                print(_("Creating ISO..."))
                self.showProgress(_("Creating ISO..."),0.80)
                yield True
                self.setBusyCursor()
                # add disc id - alternate
                subprocess.getoutput('echo \"Built by Reconstructor ' + self.appVersion + ' - Rev ' + self.updateId + ' (c) Reconstructor Team, 2006 - http://reconstructor.aperantis.com\" > \"' + os.path.join(self.customDir, "remaster_alt/.disc_id") + '\"')
                # update md5
                print(_("Updating md5 sums..."))
                subprocess.getoutput('rm \"' + os.path.join(self.customDir, "remaster_alt/") + 'md5sum.txt\"')
                # exclude isolinux directory or else when checking disc integrity it will say there are errors
                subprocess.getoutput('(cd \"' + os.path.join(self.customDir, "remaster_alt/") + '\"')
                subprocess.getoutput('find . -type f -not -name md5sum.txt -not -path \'*/isolinux/*\' -print0 | xargs -0 md5sum > md5sum.txt)')
                rootSize = self.FileSize(os.path.join(self.customDir, "root/"))
                print('%lu'%(rootSize),file=open(os.path.join(self.customDir, "remaster/casper/filesystem.size"),"w"))

                # remove existing iso
                if os.path.exists(self.buildAltCdFilename):
                    print(_("Removing existing ISO..."))
                    subprocess.getoutput('rm -Rf \"' + self.buildAltCdFilename + '\"')
                # build
                # check for description - replace if necessary
                if self.builder.get_object("entryBuildAltCdDescription").get_text() != "":
                    self.altCdDescription = self.builder.get_object("entryBuildAltCdDescription").get_text()

                self.showProgress(False,0.82)
                yield True
                # build iso according to architecture
                if self.altCdArch == "x86":
                    print(_("Building x86 ISO..."))
                    self.setBusyCursor()
                    subprocess.getoutput(self.timeCmd + ' mkisofs -o \"' + self.buildAltCdFilename + '\" -b \"isolinux/isolinux.bin\" -c \"isolinux/boot.cat\" -no-emul-boot -boot-load-size 4 -boot-info-table -V \"' + self.altCdDescription + '\" -cache-inodes -r -J -l \"' + os.path.join(self.customDir, "remaster_alt") + '\"')
                elif self.altCdArch == "PowerPC":
                    print(_("Building PowerPC ISO..."))
                    subprocess.getoutput(self.timeCmd + ' mkisofs  -r -V \"' + self.altCdDescription + '\" --netatalk -hfs -probe -map \"' + self.hfsMap + '\" -chrp-boot -iso-level 2 -part -no-desktop -hfs-bless ' + '\"' + os.path.join(self.customDir, "remaster_alt/install") + '\" -o \"' + self.buildAltCdFilename + '\" \"' + os.path.join(self.customDir, "remaster_alt") + '\"')
                elif self.altCdArch == "x86_64":
                    print(_("Building x86_64 ISO..."))
                    subprocess.getoutput(self.timeCmd + ' mkisofs -o \"' + self.buildLiveCdFilename + '\" -b \"isolinux/isolinux.bin\" -c \"isolinux/boot.cat\" -no-emul-boot -boot-load-size 4 -boot-info-table -V \"' + self.LiveCdDescription + '\" -cache-inodes -r -J -l \"' + os.path.join(self.customDir, "remaster_alt") + '\"')
                self.showProgress(False,0.95)
                yield True

        self.setDefaultCursor()
        self.setPage(self.pageFinish)
        # print(status message)
        statusMsgFinish = _('     <b>Finished.</b>     ')
        statusMsgISO = _('      <b>Finished.</b> ISO located at: ')
        if os.path.exists(self.buildAltCdFilename):
            print("ISO Located: " + self.buildAltCdFilename)
            self.builder.get_object("labelBuildComplete").set_text(statusMsgISO + self.buildAltCdFilename + '     ')
            self.builder.get_object("labelBuildComplete").set_use_markup(True)
        else:
            self.builder.get_object("labelBuildComplete").set_text(statusMsgFinish)
            self.builder.get_object("labelBuildComplete").set_use_markup(True)
        # enable/disable iso burn
        self.checkEnableBurnAltIso()

        print("Build Complete...")
        self.showProgress('Build Complete.',1)
        yield False

class AltPackageHelper:
    """AltPackageHelper - .deb package helper..."""
    def __init__(self):
        # package lists
        # ubuntu Minimal Packages - base system
        self.ubuntuMinimalPackages = ('adduser', 'alsa-base', 'alsa-utils', 'apt', 'apt-utils', 'aptitude',
                                    'base-files', 'base-passwd', 'bash', 'bsdutils', 'bzip2', 'console-setup',
                                    'console-tools', 'coreutils', 'dash', 'debconf', 'debianutils',
                                    'dhcp3-client', 'diff', 'dpkg', 'e2fsprogs', 'eject', 'ethtool',
                                    'findutils', 'gettext-base', 'gnupg', 'grep', 'gzip', 'lzma','hostname',
                                    'ifupdown', 'initramfs-tools', 'iproute', 'iputils-ping', 'less',
                                    'libc6-i686', 'libfribidi0', 'locales', 'login', 'lsb-release', 'makedev',
                                    'mawk', 'mii-diag', 'mktemp', 'module-init-tools', 'mount', 'ncurses-base',
                                    'ncurses-bin', 'net-tools', 'netbase', 'netcat', 'ntpdate', 'passwd',
                                    'pciutils', 'pcmciautils', 'perl-base', 'procps', 'python',
                                    'python-minimal', 'sed', 'startup-tasks', 'sudo', 'sysklogd',
                                    'system-services', 'tar', 'tasksel', 'zdata', 'ubuntu-keyring', 'udev',
                                    'upstart', 'upstart-compat-sysv', 'upstart-logd', 'usbutils', 'til-linux',
                                    'util-linux-locales', 'vim-tiny', 'wireless-tools', 'wpasupplicant')

        # ubuntu Standard Packages - comfortable cli system
        self.ubuntuStandardPackages = ('at', 'cpio', 'cron', 'dmidecode', 'dnsutils', 'dosfstools', 'dselect',
                                     'ed', 'fdutils', 'file', 'ftp', 'hdparm', 'info', 'inputattach',
                                     'iptables', 'iputils-arping', 'iputils-tracepath', 'logrotate', 'lshw',
                                     'lsof', 'ltrace', 'man-db', 'manpages', 'memtest86+', 'mime-support',
                                     'nano', 'parted', 'popularity-contest', 'ppp', 'pppconfig', 'pppoeconf',
                                     'psmisc', 'reiserfsprogs', 'rsync', 'strace', 'tcpdump', 'telnet', 'time',
                                     'w3m', 'wget')

        # ubuntu Server Packages - LAMP server
        self.ubuntuServerPackages = ('')
        # ubuntu Desktop Packages - default desktop system
        self.ubuntuDesktopPackages = ('acpi', 'acpi-support', 'acpid', 'alacarte', 'anacron', 'apmd',
                                    'apport-gtk', 'avahi-daemon', 'bc', 'bug-buddy', 'cdparanoia', 'cdrecord',
                                    'contact-lookup-applet', 'cupsys', 'cupsys-bsd', 'cupsys-client',
                                    'cupsys-driver-gutenprint', 'dc', 'deskbar-applet', 'desktop-file-utils',
                                    'diveintopython', 'doc-base', 'dvd+rw-tools', 'ekiga', 'eog', 'esound',
                                    'evince', 'evolution', 'evolution-exchange', 'evolution-plugins',
                                    'evolution-webcal', 'f-spot', 'file-roller', 'firefox',
                                    'firefox-gnome-support', 'foo2zjs', 'foomatic-db', 'foomatic-db-engine',
                                    'foomatic-db-hpijs', 'foomatic-filters', 'fortune-mod', 'gaim',
                                    'gcalctool', 'gconf-editor', 'gdebi', 'gdm', 'gedit', 'gimp', 'gimp-print',
                                    'gimp-python', 'gnome-about', 'gnome-app-install', 'gnome-applets',
                                    'gnome-btdownload', 'gnome-control-center', 'gnome-cups-manager',
                                    'gnome-icon-theme', 'gnome-keyring-manager', 'gnome-media', 'gnome-menus',
                                    'gnome-netstatus-applet', 'gnome-nettool', 'gnome-panel',
                                    'gnome-pilot-conduits', 'gnome-power-manager', 'gnome-session',
                                    'gnome-spell', 'gnome-system-monitor', 'gnome-system-tools',
                                    'gnome-terminal', 'gnome-themes', 'gnome-utils', 'gnome-volume-manager',
                                    'gnome2-user-guide', 'gs-esp', 'gstreamer0.10-alsa', 'gstreamer0.10-esd',
                                    'gstreamer0.10-plugins-base-apps', 'gthumb', 'gtk2-engines', 'gucharmap',
                                    'hal', 'hal-device-manager', 'hotkey-setup', 'hwdb-client-gnome',
                                    'landscape-client', 'language-selector', 'lftp', 'libgl1-mesa-glx',
                                    'libglut3', 'libgnome2-perl', 'libgnomevfs2-bin', 'libgnomevfs2-extra',
                                    'libpam-foreground', 'libpt-plugins-v4l', 'libpt-plugins-v4l2',
                                    'libsasl2-modules', 'libstdc++5', 'libxp6', 'metacity', 'min12xxw',
                                    'mkisofs', 'nautilus', 'nautilus-cd-burner', 'nautilus-sendto',
                                    'notification-daemon', 'openoffice.org', 'openoffice.org-evolution',
                                    'openoffice.org-gnome', 'pnm2ppa', 'powermanagement-interface',
                                    'readahead', 'rhythmbox', 'rss-glx', 'screen', 'screensaver-default-images',
                                    'scrollkeeper', 'serpentine', 'slocate', 'smbclient', 'sound-juicer',
                                    'ssh-askpass-gnome', 'synaptic', 'tangerine-icon-theme', 'tango-icon-theme',
                                    'tango-icon-theme-common', 'tomboy', 'totem', 'totem-mozilla', 'tsclient',
                                    'ttf-bitstream-vera', 'ttf-dejavu', 'ttf-freefont', 'ubuntu-artwork',
                                    'ubuntu-docs', 'ubuntu-sounds', 'unzip', 'update-notifier',  'vino', 
				    'wvdial', 'x-ttcidfont-conf',
                                    'xkeyboard-config', 'xorg', 'xsane', 'xscreensaver-data', 'xscreensaver-gl',
                                    'xterm', 'xvncviewer', 'yelp', 'zenity', 'zip')



    def copyPackages(self, packageList, sourcePath, destinationPath):
        for package in packageList:
            print("Copying " + package + "...")
            subprocess.getoutput("rsync -a --del --prune-empty-dirs --filter=\"+ */\" --filter=\"+ /**/" + package + "_*.deb\" --filter=\"- *\" " + sourcePath + " " + destinationPath)

# ---------- MAIN ----------

if __name__ == "__main__":
    APPDOMAIN='reconstructor'
    LANGDIR='lang'
    # locale
    locale.setlocale(locale.LC_ALL, '')
    gettext.bindtextdomain(APPDOMAIN, LANGDIR)
    #Gtk.glade.bindtextdomain(APPDOMAIN, LANGDIR)
    #Gtk.glade.textdomain(APPDOMAIN)
    gettext.textdomain(APPDOMAIN)
    gettext.install(APPDOMAIN, LANGDIR)

    # check credentials
    if os.getuid() != 0 :
        ## show non-root privledge error
        warnDlg = Gtk.Dialog(title="Reconstructor", parent=None, flags=0)
        warnDlg.set_default_size(320,150)
        warnDlg.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        warnDlg.set_icon_from_file(cur_file_dir + '/glade/app.png')
        warnDlg.vbox.set_spacing(10)
        labelSpc = Gtk.Label(label=" ")
        warnDlg.vbox.pack_start(labelSpc, expand=True, fill=True, padding=0)
        labelSpc.show()
        warnText = _("  <b>You must run with root privledges.</b>")
        infoText = _("Open a Terminal, \nand type <b>sudo python reconstructor.py</b>  ")
        label = Gtk.Label(label=warnText)
        lblInfo = Gtk.Label(label=infoText)
        label.set_use_markup(True)
        lblInfo.set_use_markup(True)
        warnDlg.vbox.pack_start(label, expand=True, fill=True, padding=0)
        warnDlg.vbox.pack_start(lblInfo, expand=True, fill=True, padding=0)
        label.show()
        lblInfo.show()
        response = warnDlg.run()
        if response == Gtk.ResponseType.OK :
            warnDlg.destroy()
            #Gtk.main_quit()
            sys.exit(0)
        # use gksu to open -- HIDES TERMINAL
        #subprocess.getoutput('gksu ' + cur_file_dir + '/reconstructor.py')
        #Gtk.main_quit()
        #sys.exit(0)
    else :
        rec = Reconstructor()
        # run gui
        Gtk.main()

