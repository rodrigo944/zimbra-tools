import getopt, sys

def pop(server, user, password):
    import poplib
    try:
        p = poplib.POP3(server)
        p.user(user)
        p.pass_(password)
        if '+OK' in p.getwelcome():
            print 'Logged in: %s' % p.getwelcome()
            sys.exit(0)
        else:
            raise Exception('Auth error: %s' % p.getwelcome())
    except Exception, e:
        print e
        sys.exit(2)

def imap(server, user, password):
    from imaplib import IMAP4
    try:
        c = IMAP4(server)
        c.login(user, password)
        c.select()
        mbox = c.list()
        c.close()
        c.logout()
        if mbox[0] == 'OK':
            print 'Logged in: OK IMAP'
            sys.exit(0)
        else:
            print 'Logged in but failed to list folders: ' % mbox
            sys.exit(1)
    except Exception, e:
        print e
        sys.exit(2)

def usage():
    print """IMAP/POP Authentication
    -s <server> Server name
    -u <login> Login name
    -p <password> Login password
    -m <method> POP or IMAP.
    -h Show this help
    """ 

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:u:p:m:h", [])
        for i in opts:
            if i[0] == '-s':
                server = i[1]
            elif i[0] == '-u':
                username = i[1]
            elif i[0] == '-p':
                password = i[1]
            elif i[0] == '-m':
                protocol = i[1]
        if protocol == 'IMAP':
            imap(server, username, password)
        else:
            pop(server, username, password)
    except getopt.GetoptError, ex:
        print ex
        usage()
        sys.exit(3)
    except NameError, n:
        print n
        usage()
        sys.exit(3)
