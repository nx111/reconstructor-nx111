#!/usr/bin/env python
#
# Reconstructor -- http://reconstructor.aperantis.com
#    Copyright (c) 2006  evan hazlett <ejhazlett@gmail.com>
#
#    PackageHelper module (downloads/sorts .debs)
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

import os
import sys
from gettext import gettext as _
import re

class PackageHelper:
	'Package Helper - downloads, sorts, and checks dependencies of .debs for Reconstructor (alternate cd creation)'
	def __init__(self, customDirectory=None, remasterDirectory=None, remasterRepoDirectory=None, remasterTempDirectory=None, distribution=None, debug=False):
		self.customDir = customDirectory
		self.altRemasterDir = remasterDirectory
		self.altRemasterRepo = remasterRepoDirectory
		self.tmpDir = remasterTempDirectory
		self.dist = distribution
		self.runningDebug = debug
		self.repoPackages = {}
		self.regexPackage = '^\s*Package:\s+(\S+)\n'
		self.regexVersion = '^\s*Version:\s+(\S+)\n'
		self.regexDepends = '^\s*Depends:\s+(\S.*)\n'
		self.regexDependPackage = '(\S+)\s*\(([<>=]+)\s(\S+)\)|(\S+)'
		# make sure vars are correct
		#assert self.customDir != None, 'Custom directory path must not be blank.'
		#assert self.dist != None, 'Distribution must not be blank.'

	# Parses Packages files and places applications and versions into dictionary
	def loadRepoPackages(self):
		# clear existing dict
		self.repoPackages.clear()
		# build regex
		rePackage = re.compile(self.regexPackage, re.IGNORECASE)
		reVersion = re.compile(self.regexVersion, re.IGNORECASE)
		# find all Packages files and load into dictionary
		for file in os.popen('find \"' + os.path.join(self.customDir, self.altRemasterDir) + '/dists/' + self.dist + '/\" -name \"Packages\" -print'):
			packageName = None
			packageVersion = None
			#print file
			for line in open(file[:-1], 'r'):
				# package
				if rePackage.match(line) != None and packageName == None:
					packageName = rePackage.match(line).group(1)
				# version
				if reVersion.match(line) != None and packageVersion == None:
					packageVersion = reVersion.match(line).group(1)
				#print packageName, packageVersion
				if packageName != None and packageVersion != None:
					# add to dict
					self.repoPackages[packageName] = packageVersion
					# reset
					packageName = None
					packageVersion = None

	# Checks whether package is in the local repository or not and returns the correct apt string
	def checkPackage(self, packageName=None, packageQualifier=None, packageVersion=None):
		# TODO: add version checking and resolving
		# make sure packages dict is created
		if len(self.repoPackages) <= 0:
			self.loadRepoPackages()
		if packageName not in self.repoPackages.keys():
			# return just the package name for apt -- no version specified
			return packageName
		else:
			# package is in repo
			return None

	# Resolves dependencies and generates dependency download list
	def resolveDependencies(self):
		#print _("Checking dependencies for extra packages...")
		packageDir = os.path.join(self.customDir, self.altRemasterDir) + '/pool/extras/'
		allDepends = ''
		dependList = ''
		reDepends = re.compile(self.regexDepends, re.IGNORECASE)
		reDependPackage = re.compile(self.regexDependPackage, re.IGNORECASE)
		rePackageVersion = re.compile(self.regexVersion, re.IGNORECASE)
		for f in os.popen('find \"' + packageDir + '\" -name *deb -print'):
			if self.runningDebug: print "Checking dependencies for: " + f[:-1]
			#print f[:-1]
			# find dependencies of package
			for line in os.popen('dpkg --info \"' + f[:-1] + '\"'):
				if reDepends.match(line) != None:
					allDepends = reDepends.match(line).group(1)
					break
			# parse depends and check
			for depend in allDepends.split(','):
				#print depend.strip()
				# regex into package and version
				packageName = None
				packageQualifier = None
				packageVersion = None
				if reDependPackage.match(depend.strip()) != None:
					if reDependPackage.match(depend.strip()).group(1) != None:
						if self.runningDebug: print "Package has version requirement: " + str(reDependPackage.match(depend.strip()).group(2)) + " " + str(reDependPackage.match(depend.strip()).group(3))
						packageName = reDependPackage.match(depend.strip()).group(1)
						packageQualifier = reDependPackage.match(depend.strip()).group(2)
						packageVersion = reDependPackage.match(depend.strip()).group(3)
					else:
						if self.runningDebug: print "Package has no version requirement: " + str(reDependPackage.match(depend.strip()).group(4))
						packageName = reDependPackage.match(depend.strip()).group(4)
						# regex for package version
						for line in os.popen('apt-cache show ' + packageName):
							if rePackageVersion.match(line) != None:
								packageVersion = rePackageVersion.match(line).group(1)
								if self.runningDebug: print "Using repository version: " + packageVersion
								break
				if packageName != None and packageQualifier != None and packageVersion != None:
					#print "Dependency: " + packageName, packageQualifier, packageVersion
					# check package and add to depend list if not in local repo
					if self.checkPackage(packageName) != None:
						if self.runningDebug: print "Extra dependency package needed: " + packageName
						dependList += packageName + ' '
						# add new package to dict
						self.repoPackages[packageName] = packageVersion
				elif packageName != None and packageVersion != None:
					# check package
					if self.checkPackage(packageName) != None:
						if self.runningDebug: print "Extra dependency package needed: " + packageName + " -- Using Repository Version: " + packageVersion
						dependList += packageName + ' '
						# add to dict
						self.repoPackages[packageName] = packageVersion
				else:
					errText = _("Error trying to resolve dependency:")
					if self.runningDebug: print errText + " " + packageName
		#print dependList
		# check for depend list -- if not empty, download packages and check again
		if dependList != '':
			# download
			self.downloadPackages(dependList)
			# check again
			self.resolveDependencies()

	# Downloads packages via apt
	def downloadPackages(self, packageList=None):
		if packageList != None:
			#print _("Downloading extra package dependencies...")
			os.popen('apt-get install -d -y -m --reinstall --allow-unauthenticated -o Dir::Cache=\"' + os.path.join(self.customDir, self.altRemasterRepo) + '/\" ' + packageList)
			#print _("Copying package dependency archives into pool...")
			os.popen('cd \"' + os.path.join(self.customDir, self.altRemasterRepo) + '/archives\" ; cp -R *.deb \"' + os.path.join(self.customDir, self.altRemasterDir) + '/pool/extras/\"')


if __name__ == "__main__":
	print "** Module not meant to be executed..."
	#print "----- Running Debug -----"
	#p = PackageHelper(customDirectory='/home/ehazlett/reconstructor/', remasterDirectory='remaster_alt', remasterRepoDirectory='remaster_alt_repo', remasterTempDirectory='tmp', distribution='edgy', debug=True)
	#p.loadRepoPackages()

	#p.resolveDependencies()

	#for x in p.repoPackages.keys():
	#    print x + ' : ' + p.repoPackages[x]
