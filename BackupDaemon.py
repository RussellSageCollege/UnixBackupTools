#! /usr/bin/env python

from __future__ import print_function
import daemon
from time import sleep
import json
import socket
from socketIO_client import SocketIO, LoggingNamespace
from helpers import readConfig, saveConfig
from multiprocessing import Process
from osBackup import performBackup

STATE_BUSY = 1
STATE_FREE = 0
BACKUP_PROCESS = None
IO = None
HOST_NAME = None
INSTANCE_KEY = False
SERVER_ADDRESS = 'localhost'
SERVER_PORT = 3000


def backup_now():
    while True:
        print('Performing a backup...')
        sleep(3)


def load_config():
    global HOST_NAME, SERVER_ADDRESS, SERVER_PORT, INSTANCE_KEY
    config = readConfig()['general']
    HOST_NAME = socket.gethostname()
    SERVER_ADDRESS = config['control_server_hostname']
    SERVER_PORT = config['control_server_port']
    try:
        INSTANCE_KEY = config['instance_key']
    except KeyError:
        INSTANCE_KEY = False


def connect_to_sio():
    print('Connecting...')
    global IO
    IO = SocketIO(SERVER_ADDRESS, SERVER_PORT, LoggingNamespace)
    IO.emit('join', {'hostname': HOST_NAME})


def verify_instance_key():
    # If we do not have an instance key from the server, get one
    if not INSTANCE_KEY:
        IO.on('key_response', on_key_response)
        IO.emit('key_request')
        IO.wait(seconds=5)
        # Reload the configuration
        print('Reloading configuration...')
        load_config()
        # If the instance key is not available at this point, abort
        if not INSTANCE_KEY: exit(1)


def emit_new_state(state):
    print('Emitting new state...')
    IO.emit('state', {
        'hostname': HOST_NAME,
        'instance_key': INSTANCE_KEY,
        'state': state
    })


def on_key_response(*args):
    for arg in args:
        # Receive the instance key
        key = json.loads(arg)['key']
        print('New instance key received: ' + key)
        conf = readConfig()
        conf['general']['instance_key'] = key
        saveConfig(conf)


def on_new_backup_task(*args):
    # Notify the server that you are busy
    emit_new_state(STATE_BUSY)
    # Build a new process for the backup job
    BACKUP_PROCESS = Process(target=backup_now)
    # Start the job
    BACKUP_PROCESS.start()
    # Join it to the pool
    BACKUP_PROCESS.join()


def on_end_backup_task(*args):
    # Terminate the backup task
    BACKUP_PROCESS.terminate()
    # Notify the server that you are free
    emit_new_state(STATE_FREE)


def main():
    # Set globals
    global BACKUP_PROCESS, STATE_BUSY, STATE_FREE
    # Load the configuration
    load_config()
    # Connect to the server
    connect_to_sio()
    # Verify that you have a good instance key
    verify_instance_key()
    # Listen for backup jobs
    IO.on('new_backup_task', on_new_backup_task)
    # Listen for cancel on job
    IO.on('end_backup_task', on_end_backup_task)
    # Notify the server that you are ready
    emit_new_state(STATE_FREE)
    # Hang out
    print('Waiting for direction...')
    IO.wait()


if __name__ == "__main__":
    main()
