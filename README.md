# Backup tools for Unix Systems

## Setup

Download

```shell
git clone https://github.com/TheSageColleges/UnixBackupTools.git;
cd UnixBackupTools/;
# Chekout to the latest tag
git checkout $(git describe --tags $(git rev-list --tags --max-count=1));
```

Configuration

```shell
cp config.example.json config.json
# Edit the configuration
vi config.json
```

## Backup root file system

To backup the root filesystem:

- add a second disk to the target machine
- swap ssh keys with the remote repository

```shell
./osBackup.py
```


## Updating

```shell
cd UnixBackupTools/;
# pull latest
git fetch --all;
# Chekout to the latest tag
git checkout $(git describe --tags $(git rev-list --tags --max-count=1));
```

## Restore an Image

Boot to a live distro and connect a flash drive with the image.gz file.

```shell
gunzip -c /path/to/backup.img.gz | dd of=/dev/sda
```

The command above will uncompress the image send the output to dd which will write the blocks to the disk `sda`.

The command may take a while to complete and you will not see any output until it has completed, be patent.
