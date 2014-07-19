#!/usr/bin/env python
from __future__ import print_function, division, absolute_import, unicode_literals
import os
import platform
import sys
import re
import shutil
import urllib2
import argparse


BLOCKHEAD = '###NULLCLICK HEAD###'
BLOCKTAIL = '###NULLCLICK TAIL###'
LINUX_HOSTPATH = '/etc/hosts'
WIN_HOSTPATH = '\\system32\\drivers\\etc\\hosts'
OSX_HOSTPATH = LINUX_HOSTPATH  
BASE_LIST = 'base.list'
CUSTOM_LIST = 'custom.list'
SINKHOLE_IP = '127.0.1.1'
SPACER = '    '
SINK_PREFIX = SINKHOLE_IP + SPACER
LIST_URL = 'https://raw.githubusercontent.com/themson/nullclick/master/base.list'

local_os = platform.system()
host_file = ''
interactive = False
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0) # Unbuffered IO for printing


def build_argparser():
    """Create ArgumentParser object, add arg options, return parse_args object."""
    parser = argparse.ArgumentParser(prog='nullclick',
                                     description='Tool for blocking click-bait sites via system host file.',
                                     epilog="* Passing no arguments invokes interactive mode.")
    parser.add_argument("-a", "--add", nargs='+',
                        help="Add domain name(s) to block list.",
                        metavar='DOMAIN', dest='domains_add')
    parser.add_argument("-r", "--remove", nargs='+',
                        help="Remove domain name(s) from block list.",
                        metavar='DOMAIN', dest='domains_remove')
    parser.add_argument("-t", "--toggle", nargs=1,
                        help="Toggle access to single domain.",
                        metavar='DOMAIN',  dest='domain_toggle')
    parser.add_argument("-p", "--print-list", action='store_true', default=False,
                        help="Print block list or block list after current actions.",
                        dest='print_list')
    parser.add_argument("-d", "--update", action='store_true', default=False,
                        help="Update block list from project repository.",
                        dest='update_list')
    parser.add_argument("-i", "--install", action='store_true', default=False,
                        help="Install block list into system host file.",
                        dest='install')
    parser.add_argument("-u", "--uninstall", action='store_true', default=False,
                        help="Remove block list from system host file.",
                        dest='uninstall')
    return parser.parse_args()


def arg_launcher(args):
    if args.uninstall:
        if remove_list() is True:
            print("\n* Block list successfully removed.")
        else:
            print("\n* No list present to uninstall.")
    if args.install:
        if install_list() is True:
            print("\n* Block list successfully installed.")
        else:
            print("\n* List already present in host file.")
    if args.update_list:
        update_list()
    if args.domains_add:
        domain_list = [domain_name for domain_name in args.domains_add if is_valid_domain(domain_name)]
        add_sites(domain_list)
    if args.domains_remove:
        domain_list = [domain_name for domain_name in args.domains_remove if is_valid_domain(domain_name)]
        remove_sites(domain_list)
    if args.domain_toggle:
        domain_name = args.domain_toggle[0]
        if is_valid_domain(domain_name):
            toggle_site(domain_name)
    if args.print_list:
        print_list()


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
4. Print current block list.
5. Update block list.
6. Exit

0. Install/Uninstall block list.
""")
    choice = ''
    valid = ('0', '1', '2', '3', '4', '5', '6')
    while choice not in valid:
        try:
            choice = raw_input('#: ')
        except Exception as e:
            choice = ''
        if choice not in valid:
            print(u"invalid choice \n")            
    return int(choice)


def interactive_launcher(choice):
    """"Take in int choice, use dict as switch to call function."""
    options = {0: install_uninstall,
               1: add_sites,
               2: remove_sites,
               3: toggle_site,
               4: print_list,
               5: update_list,
               6: exit
               }
    options[choice]()


def install_uninstall():
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
        if remove_list() is True:
            print("\n* Block list  successfully removed.")
        else:
            print("\n* No list present to uninstall.")
    elif choice == 'yes':
        if install_list() is True:
            print("\n* Block list successfully installed.")
        else:
            print("\n* Block lists already present in host file.")
    else:
        return


def is_list_present():
    """Return Bool of list presence."""
    try:
        return BLOCKHEAD in open(host_file).read()
    except IOError as e:
        print (e.args)
        exit()


def backup_hostfile():  # TODO: Review and add call in install_list
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


def file_to_list(file_path): 
    """Take in file path containing list of domain\n, one per line, return as list."""
    domain_list = []
    try:  
        with open(file_path, 'r') as list_file:
            for site in list_file: 
                domain_list.append(site.rstrip('\n'))
    except IOError as e:
            print(e.args)
            exit()
    return domain_list


def install_list():
    """Insert Block List header and footer into host file, propagate base list."""
    # backup_hostfile() TODO: Add host list backup if no block list is present. Append date to backup name.
    if not is_list_present():
        try:
            with open(host_file, 'a') as f:
                f.write(BLOCKHEAD + '\n' + BLOCKTAIL + '\n')
        except IOError as e:
            print(e.args)
            exit()
        print("\n* Block list headers installed")
        print("* Initializing base block list...")
        push_site(file_to_list(BASE_LIST))
        # print("* Initializing custom list...") # TODO: Add custom block list append on install
        # push_site(file_to_list(CUSTOM_LIST))
        return True
    else:
        return False


def remove_list():
    """Iterate host file, locate list, null out list lines. Rewrite host file."""
    if is_list_present():
        try:
            with open(host_file, 'r') as f:
                host_file_new = re.sub(BLOCKHEAD + '.*?' + BLOCKTAIL + '\n', '', f.read(), flags=re.DOTALL)
            with open(host_file, 'w') as f_new:
                f_new.write(host_file_new)
        except IOError as e:
            print(e.args)
            exit()
        return True
    else:
        return False


def push_site(domain_list):
    """Add new sites to head of block list."""
    if domain_list:
        domains_list = [domain for domain in domain_list if is_valid_domain(domain)]  # Doubled from calling function
        domain_ip_gen = (SINK_PREFIX + domain for domain in domains_list)  # Prepend sinkhole IP
        inserted_sites = (BLOCKHEAD + '\n' + '\n'.join(domain_ip_gen))
        try:
            with open(host_file, 'r') as f_in:
                host_file_new = f_in.read().replace(BLOCKHEAD, inserted_sites)
            with open(host_file, 'w') as f_out:
                f_out.write(host_file_new)
        except IOError as e:
            print(e.args)
            exit()
        print("\n* Added domain:\n{}".format('\n'.join(domain_list)))


def change_site(domain_str, option, ip=''):  # TODO: Add ability to modify sinkhole IP per site
    """Modify Site Entry
    
    Takes in domain string to change followed by new string.
    Modify site entry by replacing with update_str defined in change_options dict
    Line matched containing domain name and new options update string is placed
    """
    block_str = (SINK_PREFIX + domain_str + '\n')
    access_str = ('#' + SINK_PREFIX + domain_str + '\n')
    change_options = {'ip': ip, 'state_block': block_str, 'state_access': access_str, 'remove': ''}

    if option in change_options:
        update_str = change_options[option]
    else:
        raise ValueError("Invalid option")
    found_changed = False
    try:
        with open(host_file, 'r') as file_in:
            hostfile_new = ''
            for line in file_in:
                if line == (SINK_PREFIX + domain_str + '\n') or line == ('#' + SINK_PREFIX + domain_str + '\n'):
                    line = update_str
                    found_changed = True
                hostfile_new += line
        with open(host_file, 'w') as file_out:
            file_out.write(hostfile_new)
    except IOError as e:
        print(e.args)
        exit()
    return found_changed


def get_current_list():  # TODO: change to include sinkhole IP
    """Iterate host file, create list of tuples containing site and block state."""
    domain_list = []
    list_line = False
    if is_list_present():
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
                        line = line.lstrip(SINK_PREFIX)
                        domain_list.append((line.rstrip('\n'), state))
        except IOError as e:
            print(e.args)
            exit()
    return domain_list


def is_valid_domain(domain_name):
    """Domain name regex on single string, returns bool"""
    return bool(re.search(r'[a-zA-Z\d-]{,63}(\.[a-zA-Z\d-]{,63}).', domain_name))


def get_domain_name():
    """Prompt and return domain list

    Iterate prompt as split list.
    Checks each name against domain naming regex.
    Warning: Can return zero length list.
    """
    domains = []
    for domain_name in raw_input('\nDomain name(s)?: ').split():
        if is_valid_domain(domain_name):
            domains.append(domain_name)
        else:
            print("* Invalid domain: {}".format(domain_name))
    return domains


def add_sites(domain_list=''):
    """Push new sites onto head of list. Returns Bool if needed"""
    if is_list_present():
        if interactive:
            domain_list = get_domain_name()
        if domain_list:
            push_site(domain_list)
            return True
        else:
            print("\n* No valid domains to add.")
            return False
    else:
        print("\n* No block list present, must install list first.")
        return False


def remove_sites(remove_domains_list=''):
    """Remove list of sites from host file block list."""
    if is_list_present():
        if interactive:
            remove_domains_list = get_domain_name()
        current_domains_list = [domain_tuple[0] for domain_tuple in get_current_list()]   # List of only domain names
        for domain_name in remove_domains_list:
            if domain_name in current_domains_list:
                if change_site(domain_name, 'remove'):
                    print("\n* Removed {} from block list.".format(domain_name))
            else:
                print("\n* Domain {} not present in list. ".format(domain_name))
    else:
        print("\n* No block list present, install list first.")


def get_toggle_site():
    """Prompt user for single site, return site name str."""
    print_list()
    site_state_list = get_current_list()
    choice = ''
    while choice not in xrange(len(site_state_list)):
        try:
            choice = int(raw_input('Site Number to toggle: ')) - 1
        except Exception as e:
            choice = ''
    return site_state_list[choice][0]  # site name


def toggle_confirm():
    """Remind user this click is probably a waste of time... """
    print("Do you really need to waste your time at this site... ?")
    while 1:
        choice = raw_input("yes/no: ").lower()
        if choice == 'yes':
            return True
        elif choice == 'no':
            return False
        else:
            continue


def toggle_site(domain_choice=''):
    """Change blocked || accessible state of site via commenting out with #."""
    #TODO: FLUSH DNS CACHE / Browsing History
    site_list = get_current_list()
    if interactive:
        domain_choice = get_toggle_site()
    domain_info = [domain_data for domain_data in site_list if domain_data[0] == domain_choice]
    if domain_info:
        domain_info = domain_info[0]
    else:
        print("\n* Invalid site: {}".format(domain_choice))
        return
    domain_name = domain_info[0]
    domain_state = domain_info[1]
    if domain_state == 'BLOCKED':
        if toggle_confirm() is True:
            change_site(domain_name, 'state_access')
            print("\n* {} is now accessible".format(domain_name))
    elif domain_state == 'ACCESSIBLE':
        change_site(domain_name, 'state_block')
        print("\n* {} is now blocked.".format(domain_name))


def update_list():
    """Update host file and base block lists
    
    Load current block file into list.
    Pull updated block file from project site.
    Write new block file to disk. 
    Load new block file into list.
    Diff lists, add new domains to host_file.

    Remind user they must also have an installed list.
    """
    current_list = file_to_list(BASE_LIST)
    print("* Retrieving updated block list data...")
    try:
        new_block_list = urllib2.urlopen(LIST_URL).read()
    except Exception as e:
        print("Update Connection Error: {}".format(e.args))
        exit()
    try:
        with open(BASE_LIST, 'w') as f:
            f.write(new_block_list)
    except IOError as e:
        print(e.args)
        exit()
    new_list = file_to_list(BASE_LIST)
    diff_list = list(set(new_list) - set(current_list))
    if len(diff_list) > 0:
        push_site(diff_list)
        print("\n* List data successfully updated.")
    else:
        print("\n* List data is already up to date.")

    if is_list_present() is not True:
        print("* Note: You must install the block list for these changes to take effect.")
    
    
def print_list():
    """Print lists of sites and states."""
    if is_list_present():
        print("\n*** Current Block List ***", end='')
        for index, domain in enumerate(get_current_list()):
            print(u"{:2d} {} - {}".format(index + 1, domain[0], domain[1]))
        print('')
    else:
        print("\n* Block list not installed.")


def main():
    """Call arg launcher or menu launcher loop."""
    global interactive
    set_hostfile()

    if len(sys.argv) > 1:
        args = build_argparser()
        arg_launcher(args)
        exit()
    else:
        interactive = True
        print("\n * Entering interactive mode.")
        while 1:
            interactive_launcher(menu_choice())
    
    
if __name__ == "__main__":
    main()