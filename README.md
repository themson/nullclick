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

usage: nullclick [-h] [-a DOMAIN [DOMAIN ...]] [-r DOMAIN [DOMAIN ...]]
                 [-t DOMAIN] [-l FILE] [-p] [-d] [-i] [-u] [-s]
                 

Tool for blocking click-bait sites via system host file.


optional arguments:  
  -h, --help&nbsp;&nbsp;&nbsp;&nbsp;show this help message and exit  
  -a DOMAIN [DOMAIN ...], --add DOMAIN [DOMAIN ...]&nbsp;&nbsp;&nbsp;&nbsp;Add domain name(s) to block list.    
  -r DOMAIN [DOMAIN ...], --remove DOMAIN [DOMAIN ...]&nbsp;&nbsp;&nbsp;&nbsp;Remove domain name(s) from block list.  
  -t DOMAIN, --toggle DOMAIN&nbsp;&nbsp;&nbsp;&nbsp;Toggle access to single domain.  
  -l FILE, --list FILE&nbsp;&nbsp;&nbsp;&nbsp;Add domain names from file to block list.  
  -p, --print-list&nbsp;&nbsp;&nbsp;&nbsp;Print block list or block list after current actions.  
  -d, --update&nbsp;&nbsp;&nbsp;&nbsp;Update block list from project repository.  
  -i, --install&nbsp;&nbsp;&nbsp;&nbsp;Install block list into system host file.  
  -u, --uninstall&nbsp;&nbsp;&nbsp;&nbsp;Remove block list from system host file.  
  -s, --shell&nbsp;&nbsp;&nbsp;&nbsp;Enter interactive shell.  
