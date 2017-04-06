#!/usr/bin/python
'''
   Remove or List accounts in @deleted.accounts domain
'''
import math
import argparse
import datetime
from operator import itemgetter
from subprocess import Popen, PIPE, STDOUT

def list_accounts(show_as_table=False, retention=None):
    accounts = get_accounts(retention)
    if show_as_table:
        for (a, q, u, h) in accounts:
            print "{:<90}{:<15}{:<15}{}".format(a, q, u, h)
    else:
        for (a, q, u, h) in accounts:
            print "{},{},{},{}".format(a, q, u, h)


def human_usage(size):
    size = float(size)
    if (size==0):
        return "0B"
    units = ['B','KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB']
    p = math.floor(math.log(size, 2)/10)
    return "%.3f%s" % (size/math.pow(1024,p),units[int(p)])

def get_accounts(retention=30):
    cmd = "zmprov gqu $(zmhostname) |grep @deleted.accounts"
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    accounts = p.stdout.read()

    list_accounts = []

    for line in accounts.strip().split('\n'):
        account, quota, usage = line.split()
        if retention:
            saccount = account.split('_')
            if saccount[0].isdigit():
                try:
                    retention_period = datetime.datetime.now() + datetime.timedelta(days=-int(retention))
                    date = datetime.datetime.strptime(saccount[0], "%Y%m%d%H%M%S")
    
                    if date < retention_period:
                        list_accounts.append((account, quota, usage, human_usage(usage)))
                except:
                    continue
            #else:
            #    list_accounts.append((account, quota, usage, human_usage(usage)))
        else:
            list_accounts.append((account, quota, usage, human_usage(usage)))

    sorted(list_accounts, key=itemgetter(3))
    return list_accounts

def clean_accounts(show_confirmation=False, retention=30):    
    accounts = get_accounts(retention=retention)
    accounts_to_remove = []

    if not show_confirmation:
        print " %s accounts to be removed:" % len(accounts)
        for account in accounts:
            remove = None
            while (remove not in ['y','n']):
                remove = raw_input("Remove: %s (%s) ? (y/n) " % (account[0], account[3]))
                if remove == 'y':
                    accounts_to_remove.append(account[0])
    else:
        for account in accounts:
            accounts_to_remove.append(account[0])

    if len(accounts_to_remove):
        for account in accounts_to_remove:
            cmd = "zmprov da %s" % account
            print cmd
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)            
            stdout_data, stderr_data = p.communicate()
            if p.returncode != 0:
                raise RuntimeError("%r failed, status code %s stdout %r stderr %r" % (
                    cmd, p.returncode, stdout_data, stderr_data)
                )
    else:
        print "0 accounts to be removed."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--table", action="store_true")
    parser.add_argument('-r', "--retention", nargs='?', const=30, default=None)
    parser.add_argument('-c', "--clean", nargs='?', const=True, default=False)
    parser.add_argument('-y', "--yes", nargs='?', const=True, default=False)

    args = parser.parse_args()
    
    if args.clean:
      clean_accounts(show_confirmation=args.yes, retention=args.retention)
    else:
      list_accounts(show_as_table=args.table, retention=args.retention)
    
if __name__ == "__main__":
    main()
