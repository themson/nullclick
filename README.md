nullclick
=========

**Tool for blocking Click-Bait sites via system specific host file.**

Depends on Python 2.7.*
No third party libraries required.

**Supported:**
* Linux, OSX, Windows

**Installation:**

- Linux -
- sudo git clone https://github.com/themson/nullclick.git /opt/nullclick/
- sudo ln -fs /opt/nullclick/nullclick.py /usr/local/bin/nullclick

**Usage:**

nullclick --help

usage: nullclick [-h] [-a DOMAIN [DOMAIN ...]] [-r DOMAIN [DOMAIN ...]]
                 [-t DOMAIN] [-p] [-d] [-i] [-u]

Tool for blocking click-bait sites via system host file.

optional arguments:

  -h, --help            show this help message and exit

  -a DOMAIN [DOMAIN ...], --add DOMAIN [DOMAIN ...]
                        Add domain name(s) to block list.

  -r DOMAIN [DOMAIN ...], --remove DOMAIN [DOMAIN ...]
                        Remove domain name(s) from block list.

  -t DOMAIN, --toggle DOMAIN
                        Toggle access to single domain.

  -p, --print-list      Print block list or block list after current actions.

  -d, --update          Update block list from project repository.

  -i, --install         Install block list into system host file.

  -u, --uninstall       Remove block list from system host file.

* Passing no arguments invokes interactive mode.
