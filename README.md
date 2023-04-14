# IEC61850 Fuse

## Dependencies

- Linux
- pyiec61850
  - C compiler (gcc or clang)
  - GNU Make
  - cmake
  - graphvix
  - doxygen
  - swig
  
- python-fuse

## Build

### pyiec61850

1. git clone libiec61850
2. `cmake -DBUILD_PYTHON_BINDINGS=ON .`
3. `sudo make install`

## Run
~~~bash
env LD_LIBRARY_PATH=/usr/local/lib python3
~~~
