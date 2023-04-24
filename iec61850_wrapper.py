#!/usr/bin/env python3

"""
Pythonic wrapper for pyiec61850

"""

import iec61850
import sys

sys.stderr = open('/dev/pts/4', 'w')

def output(*args, **kwargs):
    with open('/dev/pts/4', 'w') as f:
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

    ied_error = {
        iec61850.IED_ERROR_OK: 'IED_ERROR_OK',
        iec61850.IED_ERROR_NOT_CONNECTED: 'IED_ERROR_NOT_CONNECTED',
        iec61850.IED_ERROR_ALREADY_CONNECTED: 'IED_ERROR_ALREADY_CONNECTED',
        iec61850.IED_ERROR_CONNECTION_LOST: 'IED_ERROR_CONNECTION_LOST',
        iec61850.IED_ERROR_SERVICE_NOT_SUPPORTED: 'IED_ERROR_SERVICE_NOT_SUPPORTED',
        iec61850.IED_ERROR_CONNECTION_REJECTED: 'IED_ERROR_CONNECTION_REJECTED',
        iec61850.IED_ERROR_OUTSTANDING_CALL_LIMIT_REACHED: 'IED_ERROR_OUTSTANDING_CALL_LIMIT_REACHED',
        iec61850.IED_ERROR_USER_PROVIDED_INVALID_ARGUMENT: 'IED_ERROR_USER_PROVIDED_INVALID_ARGUMENT',
        iec61850.IED_ERROR_ENABLE_REPORT_FAILED_DATASET_MISMATCH: 'IED_ERROR_ENABLE_REPORT_FAILED_DATASET_MISMATCH',
        iec61850.IED_ERROR_OBJECT_REFERENCE_INVALID: 'IED_ERROR_OBJECT_REFERENCE_INVALID',
        iec61850.IED_ERROR_UNEXPECTED_VALUE_RECEIVED: 'IED_ERROR_UNEXPECTED_VALUE_RECEIVED',
        iec61850.IED_ERROR_TIMEOUT: 'IED_ERROR_TIMEOUT',
        iec61850.IED_ERROR_ACCESS_DENIED: 'IED_ERROR_ACCESS_DENIED',
        iec61850.IED_ERROR_OBJECT_DOES_NOT_EXIST: 'IED_ERROR_OBJECT_DOES_NOT_EXIST',
        iec61850.IED_ERROR_OBJECT_EXISTS: 'IED_ERROR_OBJECT_EXISTS',
        iec61850.IED_ERROR_OBJECT_ACCESS_UNSUPPORTED: 'IED_ERROR_OBJECT_ACCESS_UNSUPPORTED',
        iec61850.IED_ERROR_TYPE_INCONSISTENT: 'IED_ERROR_TYPE_INCONSISTENT',
        iec61850.IED_ERROR_TEMPORARILY_UNAVAILABLE: 'IED_ERROR_TEMPORARILY_UNAVAILABLE',
        iec61850.IED_ERROR_OBJECT_UNDEFINED: 'IED_ERROR_OBJECT_UNDEFINED',
        iec61850.IED_ERROR_INVALID_ADDRESS: 'IED_ERROR_INVALID_ADDRESS',
        iec61850.IED_ERROR_HARDWARE_FAULT: 'IED_ERROR_HARDWARE_FAULT',
        iec61850.IED_ERROR_TYPE_UNSUPPORTED: 'IED_ERROR_TYPE_UNSUPPORTED',
        iec61850.IED_ERROR_OBJECT_ATTRIBUTE_INCONSISTENT: 'IED_ERROR_OBJECT_ATTRIBUTE_INCONSISTENT',
        iec61850.IED_ERROR_OBJECT_VALUE_INVALID: 'IED_ERROR_OBJECT_VALUE_INVALID',
        iec61850.IED_ERROR_OBJECT_INVALIDATED: 'IED_ERROR_OBJECT_INVALIDATED',
        iec61850.IED_ERROR_MALFORMED_MESSAGE: 'IED_ERROR_MALFORMED_MESSAGE',
        iec61850.IED_ERROR_SERVICE_NOT_IMPLEMENTED: 'IED_ERROR_SERVICE_NOT_IMPLEMENTED',
        iec61850.IED_ERROR_UNKNOWN: 'IED_ERROR_UNKNOWN'
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
            raise ConnectionError(f'IED error {self.ied_error[error]}')
        
    def disconnect(self):
        iec61850.IedConnection_close(self.con)
        self.con = None
    
    def connected(self):
        con = (
            self.con is not None and
            iec61850.IedConnection_getState(self.con) == iec61850.IED_STATE_CONNECTED
        )

        if not con:
            self.con = None

        return con

    def assert_connected(method):
        def _method(self, *args, **kwargs):
            if not self.connected():
                raise ConnectionError('Not connected')

            ret = method(self, *args, **kwargs)

            return ret
        return _method

    def with_connection(method):
        def _method(self, *args, **kwargs):
            self.connect()
            ret = method(self, *args, **kwargs)
            self.disconnect()

            return ret
        return _method

    def _linked_list_iterator(self, linked_list):
        output(self, linked_list)
        node = iec61850.LinkedList_getNext(linked_list)

        while node:
            yield iec61850.toCharP(node.data)
            node = iec61850.LinkedList_getNext(node)

        iec61850.LinkedList_destroy(linked_list)

    @assert_connected
    def logical_device_iterator(self):
        devices, error = iec61850.IedConnection_getLogicalDeviceList(self.con)

        if error != 0:
            raise ConnectionError('Logical device error')

        return self._linked_list_iterator(devices)

    @assert_connected
    def logical_nodes_iterator(self, logical_device):
        nodes, err = iec61850.IedConnection_getLogicalDeviceDirectory(
            self.con, logical_device
        )

        if err != 0:
            raise ConnectionError('Logical node error')

        return self._linked_list_iterator(nodes)

    @assert_connected
    def data_objects_iterator(self, logical_device, logical_node):
        objs, err = iec61850.IedConnection_getLogicalNodeDirectory(
            self.con,
            f'{logical_device}/{logical_node}',
            iec61850.ACSI_CLASS_DATA_OBJECT
        )
        
        if err != 0:
            raise ConnectionError('Data object error')

        return self._linked_list_iterator(objs)

    @assert_connected
    def get_data_directory(
            self,
            logical_device,
            logical_node,
            data_object,
            *data_attributes
    ):
        path = '/'.join([
            logical_device,
            '.'.join([logical_node, data_object, *data_attributes])
        ])

        attrs, err = iec61850.IedConnection_getDataDirectory(
            self.con,
            path
        )

        if attrs is None:
            return None

        if err != 0:
            raise ConnectionError('Data attribute error')

        return {
            value: (
                self.get_data_directory(
                    logical_device,
                    logical_node,
                    data_object,
                    *[*data_attributes, value]
                )
                or ...
            )
            for value in self._linked_list_iterator(attrs)
        }

    @with_connection
    def tree(self):
        return {
            device: {
                node: {
                    obj: self.get_data_directory(device, node, obj)
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

    @assert_connected
    def _get_value(
            self,
            logical_device,
            logical_node,
            data_object,
            *data_attributes
    ):
        data_attributes = '.'.join(data_attributes)
        path = f'{logical_device}/{logical_node}.{data_object}.{data_attributes}'

        
        output('reading', path)
        value, err = iec61850.IedConnection_readObject(
            self.con,
            path,
            iec61850.IEC61850_FC_MX
        )

        return value

    def _get_converter(self, mms_value):
        value_type = iec61850.MmsValue_getType(mms_value)
        output('type:', value_type)
        return self.converters.get(value_type)

    @with_connection
    def read_value(
            self,
            logical_device,
            logical_node,
            data_object,
            *data_attributes
    ):
      try:
          value = self._get_value(
              logical_device,
              logical_node,
              data_object,
              *data_attributes
          )

          conv = self._get_converter(value)

          if conv is None:
              return ''

          return conv(value)
      except Exception as e:
          output('read value exception', type(e))

      return ''


if __name__ == '__main__':
    from pprint import pprint
    server = MMSServer()
    breakpoint()
    server.disconnect()
