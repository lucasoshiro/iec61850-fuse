#!/usr/bin/env python3

"""
Pythonic wrapper for pyiec61850

"""

import iec61850

def output(*args, **kwargs):
    with open('/dev/pts/1', 'w') as f:
        print(*args, **kwargs, file=f)

class MMSServer:
    converters = {
        iec61850.MMS_ARRAY: None,
        iec61850.MMS_STRUCTURE: None,
        iec61850.MMS_BOOLEAN: None,
        iec61850.MMS_BIT_STRING: None,
        iec61850.MMS_INTEGER: iec61850.MmsValue_toUint32,
        iec61850.MMS_UNSIGNED: None,
        iec61850.MMS_FLOAT: iec61850.MmsValue_toFloat,
        iec61850.MMS_OCTET_STRING: None,
        iec61850.MMS_VISIBLE_STRING: None,
        iec61850.MMS_GENERALIZED_TIME: None,
        iec61850.MMS_BINARY_TIME: None,
        iec61850.MMS_BCD: None,
        iec61850.MMS_OBJ_ID: None,
        iec61850.MMS_STRING: iec61850.MmsValue_toString,
        iec61850.MMS_UTC_TIME: iec61850.MmsValue_toUnixTimestamp,
        iec61850.MMS_DATA_ACCESS_ERROR: None
    }


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
        if not self.connected():
            raise ConnectionError('Not connected')

    def _linked_list_iterator(self, linked_list):
        node = iec61850.LinkedList_getNext(linked_list)

        while node:
            yield iec61850.toCharP(node.data)
            node = iec61850.LinkedList_getNext(node)

        iec61850.LinkedList_destroy(linked_list)

    def logical_device_iterator(self):
        self._assert_connected()

        devices, error = iec61850.IedConnection_getLogicalDeviceList(self.con)

        if error != 0:
            raise ConnectionError('Logical device error')

        return self._linked_list_iterator(devices)

    def logical_nodes_iterator(self, logical_device):
        self._assert_connected()

        nodes, err = iec61850.IedConnection_getLogicalDeviceDirectory(
            self.con, logical_device
        )

        if err != 0:
            raise ConnectionError('Logical node error')

        return self._linked_list_iterator(nodes)

    def data_objects_iterator(self, logical_device, logical_node):
        self._assert_connected()

        objs, err = iec61850.IedConnection_getLogicalNodeDirectory(
            self.con,
            f'{logical_device}/{logical_node}',
            iec61850.ACSI_CLASS_DATA_OBJECT
        )
        
        if err != 0:
            raise ConnectionError('Data object error')

        return self._linked_list_iterator(objs)

    def data_attribute_iterator(self, logical_device, logical_node, data_object):
        self._assert_connected()

        attrs, err = iec61850.IedConnection_getDataDirectory(
            self.con,
            f'{logical_device}/{logical_node}.{data_object}'
        )

        if err != 0:
            raise ConnectionError('Data attribute error')

        return self._linked_list_iterator(attrs)

    def tree(self):
        return {
            device: {
                node: {
                    obj: {
                        attr: ...
                        for attr in self.data_attribute_iterator(device, node, obj)
                    }
                    for obj in self.data_objects_iterator(device, node)
                }
                for node in self.logical_nodes_iterator(device)
            }
            for device in self.logical_device_iterator()
        }

    def print_tree(self):
        tree = self.tree()

        for device, nodes in tree.items():
            print(f'LD: {device}')
            for node, objs in nodes.items():
                print(f'  LN: {node}')
                for obj, attrs in objs.items():
                    print(f'    DO: {obj}')
                    for attr in attrs:
                        print(f'      DA: {attr}')

    def _get_value(
            self,
            logical_device,
            logical_node,
            data_object,
            *data_attributes
    ):
        data_attributes = '.'.join(data_attributes)
        path = f'{logical_device}/{logical_node}.{data_object}.{data_attributes}'

        value, err = iec61850.IedConnection_readObject(
            self.con,
            path,
            iec61850.IEC61850_FC_MX            
        )

        return value

    def _get_converter(self, mms_value):
        value_type = iec61850.MmsValue_getType(mms_value)
        return self.converters.get(value_type)

    def read_value(
            self,
            logical_device,
            logical_node,
            data_object,
            *data_attributes
    ):
      value = self._get_value(
          logical_device,
          logical_node,
          data_object,
          *data_attributes
      )

      conv = self._get_converter(value)

      if conv is None:
          return None

      return conv(value)

if __name__ == '__main__':
    from pprint import pprint
    server = MMSServer()
    server.connect()
    print(server.read_value('simpleIOGenericIO', 'GGIO1', 'AnIn1', 'mag', 'f'))
    print(server.read_value('simpleIOGenericIO', 'GGIO1', 'AnIn1', 'mag', 't'))
    server.disconnect()
