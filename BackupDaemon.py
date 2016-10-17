#! /usr/bin/env python

from __future__ import print_function
import daemon
from time import sleep
import json
import socket
from socketIO_client import SocketIO, LoggingNamespace
from helpers import readConfig, saveConfig
from multiprocessing import Process, Queue
from osBackup import performBackup

STATE_BUSY = 1
STATE_FREE = 0
CURRENT_STATE = 1
BACKUP_PROCESS = None
IO = None
HOST_NAME = None
INSTANCE_KEY = False
SERVER_ADDRESS = 'localhost'
SERVER_PORT = 3000


def backup_now():
    try:
        image_path = performBackup()
        emit_backup_completed(image_path)
    except Exception:
        pass


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


def verify_instance_key():
    # If we do not have an instance key from the server, get one
    if not INSTANCE_KEY:
        IO.on('key_response', on_key_response)
        IO.emit('key_request', {'hostname': HOST_NAME})
        IO.wait(seconds=5)
        # Reload the configuration
        print('Reloading configuration...')
        load_config()
        # If the instance key is not available at this point, abort
        if not INSTANCE_KEY: exit(1)
    IO.emit('join', {'hostname': HOST_NAME, 'instance_key': INSTANCE_KEY})


def emit_new_state(state):
    print('Emitting new state...')
    global CURRENT_STATE
    CURRENT_STATE = state
    IO.emit('state', {
        'hostname': HOST_NAME,
        'instance_key': INSTANCE_KEY,
        'busy': CURRENT_STATE
    })


def emit_backup_completed(image_path):
    print('Notifying server of new image...')
    IO.emit('image', {
        'hostname': HOST_NAME,
        'instance_key': INSTANCE_KEY,
        'image': image_path
    })


def on_key_response(*args):
    for arg in args:
        # Receive the instance key
        key = json.loads(arg)['instance_key']
        print('New instance key received: ' + key)
        conf = readConfig()
        conf['general']['instance_key'] = key
        saveConfig(conf)


def on_state_response(*args):
    for arg in args:
        success = 'True' if json.loads(arg)['success'] else 'False'
        print('State notification: ' + success)
    print('Waiting for direction...')


def on_new_backup_task(*args):
    if CURRENT_STATE == STATE_FREE:
        print('Starting new backup task...')
        # Notify the server that you are busy
        emit_new_state(STATE_BUSY)
        global BACKUP_PROCESS
        try:
            # Build a new process for the backup job
            BACKUP_PROCESS = Process(target=backup_now)
            # Start the job
            BACKUP_PROCESS.start()
            # Join it to the pool
            BACKUP_PROCESS.join()
        except Exception:
            pass
        # Set the state back to free
        emit_new_state(STATE_FREE)
        return True
    else:
        return False


def on_end_backup_task(*args):
    if CURRENT_STATE == STATE_BUSY:
        # Terminate the backup task
        BACKUP_PROCESS.terminate()
        # Notify the server that you are free
        emit_new_state(STATE_FREE)
    return True


def enter_initial_ready_state():
    # Notify the server that you are ready
    emit_new_state(STATE_FREE)
    # Hang out
    IO.wait()


def main():
    # Set globals
    global BACKUP_PROCESS, STATE_BUSY, STATE_FREE
    # Load the configuration
    load_config()
    # Connect to the server
    connect_to_sio()
    # Verify that you have a good instance key
    verify_instance_key()
    # Interpret state response
    IO.on('state_response', on_state_response)
    # Listen for backup jobs
    IO.on('new_backup_task', on_new_backup_task)
    # Listen for cancel on job
    IO.on('end_backup_task', on_end_backup_task)
    # Enter the initial ready state
    enter_initial_ready_state()


if __name__ == "__main__":
    main()
