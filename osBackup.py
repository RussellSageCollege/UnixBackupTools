from __future__ import print_function
from helpers import mountDrive, mkdirP, unMountDrive, rsync, readConfig
import os, socket, datetime, sys


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


def captureDiskImageToRepo(cloneDisk, sshUser, sshHost, imagePath):
    # Helpful output
    print('[INFO] Sending image of: ' + cloneDisk + ' >>> ' + sshUser + '@' + sshHost + ':' + imagePath)
    # Run dd with the backup disk(cloneDisk) as the source. Pass the blocks through gzip to compress. Then pass to ssh to store remotely.
    disk_size = os.popen("fdisk -l | grep /dev/sda | awk 'NR==1{print $5}'").read()
    os.system(
        'pv -p -t -e -a -b ' + cloneDisk + ' | ssh ' + sshUser + '@' + sshHost + ' "gzip -9 | pv > ' + imagePath + '"'
    )


# This function performs a backup
def performBackup():
    # Get the current backup timestamp
    timeStamp = datetime.datetime.now().strftime("%A-%d-%B-%Y-%I-%M%p")
    # Get the system hostname
    hostname = socket.gethostname()
    # Read the config file
    config = readConfig()
    # Get this programs config
    config = config['osBackup']
    # Get the disk that we are trying to back up for disk image
    cloneDisk = config['disk_for_clone']
    # Get the partition that we are trying to back up for rSync
    clonePart = config['root_partition_destination']
    # The path to mount the backup disk(cloneDisk) on
    mountDir = os.path.abspath(config['mount_dir_for_clone'])
    # an array of local directories on the root FS. These dirs are rSynced to the backup disk(cloneDisk)
    dirsToBackup = config['directories_to_backup']
    # The remote repo dir on the remote host. This is were our dd images will be stored via ssh
    repoLocation = config['remote_repo_backup_location']
    # The the remote ssh user for the remote repo host
    sshUser = config['remote_repo_user']
    # The address or dns name of the remote repo
    sshHost = config['remote_repo_host']
    # Build a file path for the remote repo. This is the file path of the new image
    imagePath = os.path.join(repoLocation, 'backup-' + hostname + '-' + timeStamp + '.img.gz')
    # Helpful output
    print('[INFO] Mounting disk: ' + clonePart + ' >>> ' + mountDir)
    # Mount the backup disk(clonePart) to the mount folder(mountDir)
    mountDrive(clonePart, mountDir)
    # Helpful output
    print('[INFO] Starting sync to: ' + mountDir)
    # rSync target folders to backup mount
    syncToBackupDrive(dirsToBackup, mountDir, clonePart)
    # Helpful output
    print('[INFO] Un-mounting disk: ' + clonePart + ' --- ' + mountDir)
    # Un-mount the backup disk(clonePart) from the mount folder(mountDir)
    unMountDrive(mountDir)
    # Capture the backup disk with DD and send it to a remote repository via ssh
    captureDiskImageToRepo(cloneDisk, sshUser, sshHost, imagePath)
