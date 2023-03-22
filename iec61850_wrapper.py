#!/usr/bin/env python3

"""
Pythonic wrapper for pyiec61850

"""

import iec61850

class MMSServer:
    def __init__(self, host='localhost', port=102):
        self.host = host
        self.port = port
        self.con = None

    def connect(self):
        self.con = iec61850.IedConnection_create()
        error = iec61850.IedConnection_connect(self.con, self.host, self.port)

        if error != iec61850.IED_ERROR_OK:
            iec61850.IedConnection_destroy(self.con)
            raise ConnectionError(f'IED error {error}')
        
    def disconnect(self):
        iec61850.IedConnection_close(self.con)
        self.con = None
    
    def connected(self):
        return self.con is not None

    def _assert_connected(self):
        if not self.connected(): raise ConnectionError('')

    def logical_device_iterator(self):
        self._assert_connected()

        deviceList, error = iec61850.IedConnection_getLogicalDeviceList(self.con)
        print(error)

        device = iec61850.LinkedList_getNext(deviceList)

        while device:
            yield device

            device = iec61850.LinkedList_getNext(device)

        iec61850.LinkedList_destroy(deviceList)

if __name__ == '__main__':
    server = MMSServer()
    server.connect()
    devices = [*server.logical_device_iterator()]
    for device in devices:
        print("LD: %s" % iec61850.toCharP(device.data))
    server.disconnect()
