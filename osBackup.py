#! /usr/bin/env python

from __future__ import print_function
from helpers import mountDrive, mkdirP, unMountDrive, rsync, readConfig
import os
import socket
import datetime


class osBackup:
    # rSync the directories to the backup disk
    def syncToBackupDrive(self, dirsToBackup, backupMount):
        # Loop over directories that should be synced
        for sourceDir in dirsToBackup:
            # Normalize the path
            sourceDir = os.path.abspath(sourceDir)
            # Ensure that the backup target dir exists
            if os.path.isdir(sourceDir):
                # Ensure that we are not just backing up the root mount, this is bad since we don't need /dev and /tmp and other dirs.
                if not sourceDir == '/':
                    # Build the destination path
                    destination = os.path.normpath(backupMount + '/' + sourceDir)
                    # Make sure we are not syncing the backup mount to the backup location
                    if not sourceDir == backupMount:
                        if not sourceDir == destination:
                            # Check to make sure that the destination dir exists
                            if not os.path.isdir(destination):
                                # If it does not exists make it
                                print('[INFO] Creating >>> ' + destination)
                                # mkdirP(destination)
                            # helpful output
                            print('[INFO] Syncing ' + sourceDir + ' >>> ' + destination)
                            # Run our rSync function
                            # rsync(sourceDir, destination)
                        else:
                            print(
                                '[WARN] Not syncing... source is the same as destination! ' + sourceDir + ' === ' + destination)
                    else:
                        print(
                            '[WARN] Not syncing backup disk mount. to backup mount. That\'s some inception level stuff!')
                else:
                    print('[WARN] Not syncing root of filesystem. Please specify more specific directories.')
            else:
                print('[WARN] Path Not Found: ' + sourceDir + ' was selected for sync but was not found.')

    # Captures a compressed disk image and SSH's the image to a remote repo
    def captureDiskImageToRepo(self, cloneDisk, sshUser, sshHost, imagePath):
        # Helpful output
        print('[INFO] Sending image of: ' + cloneDisk + ' >>> ' + sshUser + '@' + sshHost + ':' + imagePath)
        # Run dd with the backup disk(cloneDisk) as the source. Pass the blocks through gzip to compress. Then pass to ssh to store remotely.
        os.system(
            'dd bs=1M if=' + cloneDisk + ' | gzip -9 | ssh ' + sshUser + '@' + sshHost + ' "cat > ' + imagePath + '"'
        )

    # The main function
    def main(self):
        # Get the current backup timestamp
        timeStamp = datetime.datetime.now().strftime("%A-%d-%B-%Y-%I-%M%p")
        # Get the system hostname
        hostname = socket.gethostname()
        # Read the config file
        config = readConfig()
        # Get this programs config
        config = config['osBackup']
        # Get the disk that we are trying to back up
        cloneDisk = config['disk_for_clone']
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
        print('[INFO] Mounting disk: ' + cloneDisk + ' >>> ' + mountDir)
        # Mount the backup disk(cloneDisk) to the mount folder(mountDir)
        mountDrive(cloneDisk, mountDir)
        # Helpful output
        print('[INFO] Starting sync to: ' + mountDir)
        # rSync target folders to backup mount
        self.syncToBackupDrive(dirsToBackup, mountDir)
        # Helpful output
        print('[INFO] Un-mounting disk: ' + cloneDisk + ' --- ' + mountDir)
        # Un-mount the backup disk(cloneDisk) from the mount folder(mountDir)
        unMountDrive(mountDir)
        # Capture the backup disk with DD and send it to a remote repository via ssh
        self.captureDiskImageToRepo(cloneDisk, sshUser, sshHost, imagePath)


# Run the main function
osBackup().main()
