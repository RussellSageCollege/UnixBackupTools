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


# Updating

```shell
cd UnixBackupTools/;
# pull latest
git fetch --all;
# Chekout to the latest tag
git checkout $(git describe --tags $(git rev-list --tags --max-count=1));
```