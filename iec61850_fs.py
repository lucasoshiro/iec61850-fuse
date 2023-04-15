#!/usr/bin/env python3


import fuse
import stat
from time import time
# import logging

from os import path as pth, sep
from iec61850_wrapper import MMSServer

# logging.basicConfig(filename='/dev/pts/4', encoding='utf-8', level=logging.INFO)

fuse.fuse_python_api = (0, 2)

def output(*args, **kwargs):
    with open('/dev/pts/4', 'w') as f:
        print(*args, **kwargs, file=f)

def dict_find(d, path):
    output('dict_find', path)
    if path == []: return d
    assert isinstance(d, dict)
    assert isinstance(path, list)

    child, *other = path
    child_tree = d.get(child)

    return child_tree and dict_find(child_tree, other)

class MyStat(fuse.Stat):
   def __init__(self):
       output('aaa')
       self.st_mode = stat.S_IFDIR | 0o755
       self.st_ino = 0
       self.st_dev = 0
       self.st_nlink = 2
       self.st_uid = 0
       self.st_gid = 0
       self.st_size = 4096
       self.st_atime = 0
       self.st_mtime = 0
       self.st_ctime = 0
       output('bbb')

class Iec61850FS(fuse.Fuse):
    def __init__(self, host='localhost', port=102, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)

        self.server = MMSServer(host, port)
        self.server.connect()

        self.tree = self.server.tree()

    def _path_contents(self, path):
        output('_path_contents')

        output(path)
        path = pth.normpath(path)
        output(path)
        path = [*filter(None, path.split(sep))]
        output(path)
        output('tree', self.tree)

        contents = dict_find(self.tree, path)
        return contents

    def readdir(self, path, offset):
        output('readdir')

        contents = self._path_contents(path)

        assert isinstance(contents, dict) or isinstance(contents, list)

        for content in ('.', '..', *contents):
            yield fuse.Direntry(content)

    def getattr(self, path):
        output('getattr')
        st = MyStat()

        output('ccc')
        contents = self._path_contents(path)

        output('contents', contents)

        if contents is None:
            return -errno.ENOENT

        if isinstance(contents, dict):
            st.st_nlink = len(contents)
            return st

        st.st_atime = int(time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime
        st.st_nlink = 1
        st.st_mode = stat.S_IFREG | 0o666

        output('xablau')
        return st

    # def read(self, path, size, offset):
    #     output('AAA', path)
    #     path = pth.normpath(path)
    #     output('BBB', path)
    #     path = path.split(sep)[1:]
    #     output('CCC', path)

    #     try:
    #         obj = self.server.read_object(*path)
    #     except Exception as e:
    #         output(e)

    #     output('DDD', obj)
    #     slen = len(obj)
    #     output('EEE', slen)
    #     if offset < slen:
    #         if offset + size > slen:
    #             size = slen - offset
    #         buf = obj[offset:offset+size]
    #     else:
    #         buf = b''
    #     output('FFF', str(buf))
    #     return buf

