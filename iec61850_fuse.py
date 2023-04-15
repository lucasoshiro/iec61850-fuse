#!/usr/bin/env python3

from iec61850_fs import Iec61850FS


if __name__ == '__main__':
    fs = Iec61850FS(
        version="%prog 1.0",
        usage="um dois tres quatro",
        dash_s_do='setsingle'
    )

    fs.parse(errex=1)
    fs.main()
