# bake.py
# Create the HiSPARC installer.

import os
import sys

from datetime  import datetime
from userinput import *
from nsis      import *

#files created will always be put in the "\bake\releases" directory
RELEASE_DIRECTORY = "./releases"

input = userInput()
nsiHandling = nsiHandling()

print "\nWelcome to the HiSPARC bake script!\n"
adminVersion  = input.getVersion("administrator")
userVersion   = input.getVersion("user")
releaseNumber = input.getVersion("release")

tNow = datetime.today()
releaseDate = "%d%02d%02d_%02d%02d%02d" % (tNow.year, tNow.month, tNow.day, tNow.hour, tNow.minute, tNow.second)

#check if the RELEASE_DIRECTORY exists, if not create it
if not os.access(RELEASE_DIRECTORY, os.F_OK):
    os.makedirs(RELEASE_DIRECTORY)

#compile the administrator software first
if os.path.exists("%s/adminUpdater_v%s.exe" % (RELEASE_DIRECTORY, adminVersion)):
    print "Administrator installer already exists, not creating a new one!"
else:
    try:
        nsiHandling.compileNSI("./nsisscripts/adminupdater/admininstaller.nsi",
        ["ADMIN_VERSION=%s" % adminVersion])
    except:
        print "ERROR: Compilation could not be finished!"
        sys.exit

#compile the user software
if os.path.exists("%s/userUnpacker_v%s.exe" % (RELEASE_DIRECTORY, userVersion)):
    print "User unpacker already exists, not creating a new one!"
else:
    try:
        nsiHandling.compileNSI("./nsisscripts/userunpacker/userunpacker.nsi",
        ["USER_VERSION=%s" % userVersion])
    except:
        print "ERROR: Compilation could not be finished!"
        sys.exit

#compile the main installer
try:
    nsiHandling.compileNSI("./nsisscripts/maininstaller/hisparcinstaller.nsi",
    ["ADMIN_VERSION=%s" % adminVersion]+["USER_VERSION=%s" % userVersion]+["RELEASE=%s" % releaseNumber]+["RELEASE_DATE=%s" % releaseDate])
except:
    print "ERROR: Compilation could not be finished!"
    sys.exit

print "\nFinished compilation of version %s.%s.%s.\n" % (adminVersion, userVersion, releaseNumber)