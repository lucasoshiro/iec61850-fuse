#!/usr/bin/env python3


import fuse
import stat
from time import time
from os import path as pth, sep
import os
from iec61850_wrapper import MMSServer
import iec61850
import sys
import errno

sys.stderr = open('/dev/pts/4', 'w')

# logging.basicConfig(filename='/dev/pts/4', encoding='utf-8', level=logging.INFO)

fuse.fuse_python_api = (0, 2)

hello_str = b'minha terra tem palmeiras onde canta o sabia\n'

def output(*args, **kwargs):
    with open('/dev/pts/4', 'w') as f:
        print(*args, **kwargs, file=f)

def dict_find(d, path):
    if path == []: return d
    assert isinstance(d, dict)
    assert isinstance(path, list)

    child, *other = path
    child_tree = d.get(child)

    return child_tree and dict_find(child_tree, other)

class MyStat(fuse.Stat):
   def __init__(self):
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

class Iec61850FS(fuse.Fuse):
    def __init__(self, host='localhost', port=102, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)

        self.server = MMSServer(host, port)
        self.tree = self.server.tree()


    def _path_contents(self, path):
        path = pth.normpath(path)
        path = [*filter(None, path.split(sep))]

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

        contents = self._path_contents(path)

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

        path = pth.normpath(path).split(sep)[1:]

        obj = bytes(str(self.server.read_value(*path)), 'utf-8')

        st.st_size = len(obj)
        # output('len1: ', st.st_size)

        return st

    # def open(self, path, flags):
    #     accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
    #     if (flags & accmode) != os.O_RDONLY:
    #         return -errno.EACCES

    def read(self, path, size, offset):
        output('read')
        path = pth.normpath(path).split(sep)[1:]

        obj = bytes(str(self.server.read_value(*path)), 'utf-8')
        slen = len(obj)

        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = obj[offset:offset+size]
        else:
            buf = b''
        return buf
