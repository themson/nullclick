#!/usr/bin/env python
from __future__ import print_function, division, absolute_import, unicode_literals
import os
import platform
import sys
import re
import shutil
import urllib2



BLOCKHEAD = '###ClickBait HEAD###'
BLOCKTAIL = '###ClickBait TAIL###'
LINUX_HOSTPATH = '/etc/hosts'
WIN_HOSTPATH = '\\system32\\drivers\\etc\\hosts'
OSX_HOSTPATH = LINUX_HOSTPATH  
BASE_LIST = 'base.list'
SINKHOLE_IP = '127.0.1.1'
SPACER = '    '
SINKPREFIX = SINKHOLE_IP + SPACER
LIST_URL = 'https://raw.githubusercontent.com/EOA/nullclick/master/base.list'

local_os = platform.system()
host_file = ''
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0) # Unbuffered IO for printing


def set_hostfile():
    """Set file to manipulate based off OS environment."""
    global host_file
    if local_os.lower() == 'linux':
        host_file = LINUX_HOSTPATH
    elif local_os.lower() == 'darwin':
        host_file = OSX_HOSTPATH
    elif local_os.lower() == 'windows':
        host_file = os.environ['WINDIR'] + WIN_HOSTPATH
    else:
        print (u"Unrecognized host OS")
        exit()


def menu_choice():
    """"Print options menu, take in user choice."""
    print (u"""
1. Add site to block list.
2. Remove site from block list. 
3. Toggle site state.
4. Update block list.
5. Print all block list.
6. Exit

0. Install/Uninstall block list.
""")
    choice = ''
    valid = ('0','1', '2', '3', '4', '5', '6')
    while choice not in valid:
        try:
            choice = raw_input('#: ')
        except:
            choice = ''
        if choice not in valid:
            print(u"invalid choice \n")            
    return int(choice)


def launcher(choice):
    """"Take in int choice, use dict as switch to call function."""
    options = {0 : install_uninstall,
               1 : add_site,
               2 : remove_site,
               3 : toggle_site,
               4 : update_list,
               5 : print_list,
               6 : exit
               }
    options[choice]()


def install_uninstall(**kwargs):
    """Check for block list headers, if present uninstall. If not, install."""
    list_present = is_list_present()
    choice = ''
    while choice not in ['yes', 'no']:
        if list_present:
            print(u"\n* Uninstall block list?")
        else:
            print(u"\n* Install block list?")
        choice = raw_input('yes/no ?: ').lower()
    if list_present and choice == 'yes':
        remove_list()
    elif choice == 'yes':
        initialize_list()
    else:
        return


def is_list_present():
    """Return Bool of list presence."""
    try:
        return BLOCKHEAD in open(host_file).read()
    except IOError as e:
        print (e.args)
        exit()


def backup_hostfile(): #TODO: Review and add call in initialize_list or 
    """Backups up host file before injection of block list. Called from initialize_list()"""
    host_file_backup = '%s.backup' % host_file
    if os.path.exists(host_file_backup):
        import filecmp
        cmp_result = filecmp.cmp(host_file, host_file_backup)
        list_installed = is_list_present()
        if not cmp_result and not list_installed:
            shutil.copyfile(host_file, host_file_backup)
    else:
        try:
            shutil.copy2(host_file, host_file_backup)
        except IOError as e:
            print(u"Unable to back up hosts file: \n{}".format(e.args))
            exit()


def initialize_list():
    """Insert Block List header and footer into host file, propagate base list."""
    # backup_hostfile() TODO: Add user prompting for back up, append date to hostfile name
    try:
        with open(host_file, 'a') as hostf:
            hostf.write(BLOCKHEAD + '\n' + BLOCKTAIL + '\n')
    except IOError as e:
        print(e.args)
        exit()
    print("\n* Block list headers installed")         
    print("* Initializing block list")
    push_site(file_to_list(BASE_LIST))        


def file_to_list(file_path): 
    """Take in file path containing list of domain\n, one per line, return as list."""
    domain_list = []
    try:  
        with open(file_path, 'r') as list_file: #TODO: Consider moving to list_file.read().join() on new line    
            for site in list_file: 
                domain_list.append(site)
    except IOError as e:
            print(e.args)
            exit()
    return domain_list


def remove_list():
    """Iterate host file, locate list, null out list lines. Rewrite host file."""
    try:
        with open(host_file, 'r') as f:
            host_file_new = re.sub(BLOCKHEAD + '.*?' + BLOCKTAIL + '\n', '', f.read(), flags=re.DOTALL)
        with open(host_file, 'w') as fnew:
            fnew.write(host_file_new) 
    except IOError as e:
        print(e.args)
        exit()
    print("\n* Block list removed.")
    

def push_site(domain_list):
    """Add new sites to head of block list."""
    ip_domain_list = []
    for domain in domain_list:# Prepend IP 
        ip_domain_list.append(SINKPREFIX + domain)
    inserted_sites = BLOCKHEAD + '\n' + ''.join(ip_domain_list).rstrip('\n')
    try:
        with open(host_file, 'r') as fin:
            hostfile_new = fin.read().replace(BLOCKHEAD, inserted_sites)
        with open(host_file, 'w') as fout:
            fout.write(hostfile_new)   
    except IOError as e:
        print(e.args)
        exit()
    print("\n* Added to block list:\n{}".format(''.join(domain_list)))    
    

def change_site(domainstr, update):
    """Modify Site Entry
    
    Takes in domain string to change followed by new string.
    Modify access state by passing # plus current string 
    Removes site from list by passing Null string 
    """
    #TODO: Modify to only take in change options (ip, state, remove)
    #TODO: Add ability to modify sinkhole IP per site
    match = False
    try:
        with open(host_file, 'r') as fin:
            hostfile_new = ''
            for line in fin:
                if line.endswith(domainstr + '\n'):
                    line = update
                    match = True
                hostfile_new += line
        with open(host_file, 'w') as fout:
            fout.write(hostfile_new)   
    except IOError as e:
        print(e.args)
        exit()
    return match 


def get_current_list():
    """Iterate host file, create list of tuples containing site and block state."""
    domain_list = []
    list_line = False
    try:
        with open(host_file, 'r') as f:
            for line in f:
                if line == BLOCKHEAD + '\n':
                    list_line = True
                    continue
                if line == BLOCKTAIL + '\n':
                    print('')
                    break 
                if list_line:
                    state = 'BLOCKED'
                    if line.startswith('#'):
                        line = line.lstrip('#')
                        state = 'ACCESSIBLE'
                    line = line.lstrip(SINKPREFIX)
                    domain_list.append((line.rstrip('\n'), state))    
            else:
                print("\n* Block list not found.")
    except IOError as e:
        print(e.args)
        exit()
    return domain_list


def get_domain_name():
    """Prompt for and return domain name, check against valid naming regex."""
    domain = []
    domain.append(raw_input('\nDomain name?: '))
    if re.search(r'[a-zA-Z\d-]{,63}(\.[a-zA-Z\d-]{,63}).', domain[0]):
        return domain
    else:
        print("Invalid domain name")
        exit()
        

def add_site():
    """Push new site onto head of list."""
    domain = get_domain_name()
    push_site(domain)


def remove_site():
    """Remove site from list."""
    domain = get_domain_name()[0]
    if change_site(domain, ''):
        print("\n* Removed {} from block list.".format(domain))
    else:
        print("\n* Domain %s not present in list. ".format(domain))


def toggle_site():
    """Change blocked || accessible state of site via commenting out with #."""
    print_list()
    site_list =  get_current_list()
    valid = False
    choice = ''
    while not valid:
        try:
            choice = int(raw_input('Site Number to toggle: '))
            valid  = choice in range(len(site_list))
        except:
            choice = ''
            valid = False
        if not valid:
            print("invalid choice \n")
    state = site_list[choice][1]
    if state == 'BLOCKED':            
        change_site(site_list[choice][0], '#' + SINKPREFIX + site_list[choice][0] + '\n')
        print("\n* {} is now accessible".format(site_list[choice][0])) 
    elif state == 'ACCESSIBLE':
        change_site('#' + SINKPREFIX + site_list[choice][0], SINKPREFIX + site_list[choice][0] + '\n')
        print("\n* {} is now blocked.".format(site_list[choice][0]))  
    #TODO: FLUSH DNS CACHE / Browsing History


def update_list():
    """Update hostfile and base block lists
    
    Load current block file into list.
    Pull updated block file from project site.
    Write new block file to disk. 
    Load new block file into list.
    Diff lists, add new to host_file.
    """
    current_list = file_to_list(BASE_LIST)
    try:
        new_block_list = urllib2.urlopen(LIST_URL).read()
    except Exception as e:
        print(e.args)
        exit()
    try:
        with open(BASE_LIST, 'w') as f:
            f.write(new_block_list)
    except IOError as e:
        print(e.args)
        exit()
    new_list = file_to_list(BASE_LIST)
    diff_list =  list( set(new_list) - set(current_list) )
    if len(diff_list) > 0:
        push_site(diff_list)
        print("\n* List successfully updated.")
    else:
        print("\n* List is already up to date.")
    
    
def print_list():
    """Print lists of sites and states."""
    print("\n*** Current Block List ***", end='')
    for index, domain in enumerate(get_current_list()):
        print(u"{:2d} {} - {}".format(index, domain[0], domain[1]))
    print('')


def main():
    """Call menu and function launcher loop"""
    set_hostfile()
    while 1:
        launcher(menu_choice())
    
    
if __name__ == "__main__":
    main()
