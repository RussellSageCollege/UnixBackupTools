from __future__ import print_function

import os
import errno
import json


# read config.json
def readConfig():
    # Open the config file
    with open('config.json') as data_file:
        # return the json object as a python object
        return json.load(data_file)

# save the config file
def saveConfig(config):
    # Open the config file
    with open('config.json', 'w') as configFile:
        # Dump the json to the config file
        json.dump(config, configFile)


# Helper function that performs an mkdir -p
def mkdirP(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# mount wrapper
def mountDrive(disk, folder):
    # Open a shell and run the mount command
    os.system('mount ' + disk + ' ' + folder + ';')


# unmount wrapper
def unMountDrive(folder):
    # Open a shell and run the unmount command
    os.system('umount ' + folder + ';')


# rsync wrapper
def rsync(source, destination):
    # Open a shell and run an rsync command
    os.system('rsync -aH --delete --progress' + source + ' ' + destination + ';')
