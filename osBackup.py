#! /usr/bin/env python

from __future__ import print_function
import os
import json
import socket
import datetime


class osBackup:
    CONFIG_FILE_PATH = 'config.json'

    # read config.json
    def readConfig(self):
        with open(self.CONFIG_FILE_PATH) as data_file:
            return json.load(data_file)

    # mount wrapper
    def mountDrive(self, disk, folder):
        os.system('mount ' + disk + ' ' + folder + ';')

    # unmount wrapper
    def unMountDrive(self, folder):
        os.system('umount ' + folder + ';')

    # rsync wrapper
    def rsync(self, source, destination):
        os.system('rsync -avP ' + source + ' ' + destination + ';')

    # rsync the directories to the backup disk
    def syncToBackupDrive(self, config):
        for source in config.backup_dirs:
            if os.path.isdir(source):
                if not source == '/':
                    destination = config.destination_mount + source
                    if not os.path.isdir(destination):
                        os.makedirs(destination)
                    print('[INFO] Syncing ' + source + ' >>> ' + destination)
                    self.rsync(source, destination)
                else:
                    print('[WARN] Not syncing root of filesystem. Please specify more specific directories.')
            else:
                print('[WARN] Path Not Found: ' + source + ' was selected for sync but was not found.')

    # Captures a compressed disk image and SSH's the image to a remote repo
    def captureDiskImageToRepo(self, config):
        # Get the current time stamp
        timeStamp = datetime.datetime.now().strftime("%A-%d-%B-%Y-%I-%M%p")
        os.system(
            'dd bs=1M if=' + config.destination_disk + ' | gzip -9 | ssh ' # Pipe DD to gzip then to SSH
            + config.remote_host_user + '@' + config.remote_host
            + ' "cat > ' + config.remote_file_location # Cat the incoming data to the backup file
            + 'backup-' + socket.gethostname()
            + '-' + timeStamp + '.img.gz"'
        )

    # The main function
    def main(self):
        # Read the config file
        config = self.readConfig()
        self.mountDrive(config.destination_disk, config.destination_mount)
        self.syncToBackupDrive(config)
        self.unMountDrive(config.destination_mount)

# Run the main function
osBackup().main()