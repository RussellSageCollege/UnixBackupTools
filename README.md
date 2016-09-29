# Backup tools for Unix Systems

## Setup

configuration

```
cp config.example.json config.json
# Edit the configuration
vi config.json
```

## Backup root file system

To backup the root filesystem:

- add a second disk to the target machine
- swap ssh keys with the remote repository

```
./osBackup.py
```
