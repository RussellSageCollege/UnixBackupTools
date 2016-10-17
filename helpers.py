from __future__ import print_function
import os, sys, errno, json


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
    os.system('rsync -aH --delete --info=progress2 --no-i-r ' + source + ' ' + destination + ';')


# rSync the directories to the backup disk
def syncToBackupDrive(dirsToBackup, backupMount, cloneDisk):
    # Loop over directories that should be synced
    for sourceDir in dirsToBackup:
        # Normalize the path
        sourceDir = os.path.abspath(sourceDir)
        # Ensure that we are not just backing up the root mount, this is bad since we don't need /dev and /tmp and other dirs.
        if not sourceDir == '/':
            # Make sure we are not syncing the backup mount to the backup location
            if not sourceDir == backupMount:
                # Build the destination path
                destination = os.path.normpath(backupMount + '/' + sourceDir)
                if not sourceDir == destination:
                    # Ensure that the backup disk is mounted before we proceed
                    if os.path.ismount(backupMount):
                        # Are we backing up a dir?
                        if os.path.isdir(sourceDir):
                            destinationIsValid = True
                            isDir = True
                            # Check to make sure that the destination dir exists
                            if not os.path.isdir(destination):
                                # If it does not exists make it
                                print('[INFO] Creating >>> ' + destination)
                                mkdirP(destination)

                        elif os.path.isfile(sourceDir) or os.path.islink(sourceDir):
                            destinationIsValid = True
                            isDir = False
                        else:
                            print(
                                '[WARN] Path Not Found: ' + sourceDir + ' was selected for sync but was not found.')
                            destinationIsValid = False
                            isDir = False

                        if destinationIsValid:
                            # helpful output
                            if isDir:
                                print('[INFO] Syncing Directory ' + sourceDir + ' >>> ' + destination)
                            else:
                                print('[INFO] Syncing File ' + sourceDir + ' >>> ' + destination)
                            # Run our rSync function
                            rsync(sourceDir, destination)
                    else:
                        print(
                            '[ERROR] Not syncing... destination disk is not mounted! ' + cloneDisk + ' >>> ' + backupMount + ' --- Exiting!')
                        sys.exit(1)
                else:
                    print(
                        '[WARN] Not syncing... source is the same as destination! ' + sourceDir + ' === ' + destination)
            else:
                print(
                    '[WARN] Not syncing backup disk mount. to backup mount. That\'s some inception level stuff!')
        else:
            print('[WARN] Not syncing root of filesystem. Please specify more specific directories.')

            # Captures a compressed disk image and SSH's the image to a remote repo


def captureDiskImageToRepo(cloneDisk, sshUser, sshHost, imagePath, network_compression_level=1,
                           repo_compression_level=1, repo_decompress=False):
    # Helpful output
    print('[INFO] Sending image of: ' + cloneDisk + ' >>> ' + sshUser + '@' + sshHost + ':' + imagePath)
    # Run dd with the backup disk(cloneDisk) as the source. Pass the blocks through gzip to compress. Then pass to ssh to store remotely.
    if repo_decompress:
        os.system(
            'pv -p -t -e -a -b ' + cloneDisk + '| pigz -' + str(
                network_compression_level) + ' | ssh ' + sshUser + '@' + sshHost + ' "unpigz -c | pv -q > ' + imagePath + '"'
        )
    else:
        # If the network compression level is more than the server side compression level set the server side compression level to 0
        if (network_compression_level >= repo_compression_level):
            repo_compression_level = 0

        # If the server side compression level is 0
        if repo_compression_level == 0:  # At this time, this one will run, since the default levels will result in repo_compression equalling 0
            # Don't bother running Gzip on the server side
            os.system(
                'pv -p -t -e -a -b ' + cloneDisk + '| pigz -' + str(
                    network_compression_level) + ' | ssh ' + sshUser + '@' + sshHost + ' "pv -q > ' + imagePath + '"'
            )
        else:
            # Run the backup through GZip on the server
            os.system(
                'pv -p -t -e -a -b ' + cloneDisk + '| pigz -' + str(
                    network_compression_level) + ' | ssh ' + sshUser + '@' + sshHost + ' "unpigz -c | pigz -' + str(
                    repo_compression_level) + ' | pv -q > ' + imagePath + '"'
            )
