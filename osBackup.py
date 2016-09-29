#! /usr/bin/env python

from __future__ import print_function
import os
import json
import socket
import datetime
import errno


class osBackup:
    CONFIG_FILE_PATH = 'config.json'

    # read config.json
    def readConfig(self):
        # Open the config file
        with open(self.CONFIG_FILE_PATH) as data_file:
            # return the json object as a python object
            return json.load(data_file)

    # Helper function that performs an mkdir -p
    def mkdirP(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    # mount wrapper
    def mountDrive(self, disk, folder):
        # Open a shell and run the mount command
        os.system('mount ' + disk + ' ' + folder + ';')

    # unmount wrapper
    def unMountDrive(self, folder):
        # Open a shell and run the unmount command
        os.system('umount ' + folder + ';')

    # rsync wrapper
    def rsync(self, source, destination):
        # Open a shell and run an rsync command
        os.system('rsync -avP ' + source + ' ' + destination + ';')

    # rsync the directories to the backup disk
    def syncToBackupDrive(self, config):
        # Loop over directories that should be synced
        for source in config.backup_dirs:
            # Ensure that the backup target dir exists
            if os.path.isdir(source):
                # Ensure that we are not just backing up the root mount, this is bad since we don't need /dev and /tmp and other dirs.
                if not source == '/':
                    # Build the destination path
                    destination = config.destination_mount + source
                    # Check to make sure that the destination dir exists
                    if not os.path.isdir(destination):
                        # If it does not exists make it
                        self.mkdirP(destination)
                    # helpful output
                    print('[INFO] Syncing ' + source + ' >>> ' + destination)
                    # Run our rsync function
                    self.rsync(source, destination)
                else:
                    print('[WARN] Not syncing root of filesystem. Please specify more specific directories.')
            else:
                print('[WARN] Path Not Found: ' + source + ' was selected for sync but was not found.')

    # Captures a compressed disk image and SSH's the image to a remote repo
    def captureDiskImageToRepo(self, config):
        # Get the current time stamp
        timeStamp = datetime.datetime.now().strftime("%A-%d-%B-%Y-%I-%M%p")
        # The os.system call below runs dd and pipes to gzip to compress on the fly while which is then piped to
        # a ssh command that stores the incoming compressed image
        os.system(
            'dd bs=1M if=' + config.destination_disk + ' | gzip -9 | ssh '  # Pipe DD to gzip then to SSH
            + config.remote_host_user + '@' + config.remote_host
            + ' "cat > ' + config.remote_file_location  # Cat the incoming data to the backup file
            + 'backup-' + socket.gethostname()
            + '-' + timeStamp + '.img.gz"'
        )

    # The main function
    def main(self):
        # Read the config file
        config = self.readConfig()
        # Mount the backup drive to the mount folder
        self.mountDrive(config.destination_disk, config.destination_mount)
        # rSync target folders to backup mount
        self.syncToBackupDrive(config)
        # unmount the backup drive from the mount folder
        self.unMountDrive(config.destination_mount)
        # Capture a disk image of the backup disk using DD and ssh it to a remote host while compressing it.
        self.captureDiskImageToRepo(config)


# Run the main function
osBackup().main()
