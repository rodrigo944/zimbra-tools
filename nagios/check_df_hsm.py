#!/usr/bin/python
import getopt
import subprocess as sb
import sys

def check_error(proc, command):
    if proc.returncode == 1:
        raise RuntimeError('Error subprocessing command: %s' % command)
        
def usage():
    print """Check volumes free spaces as one
    -s <Gigabytes> Safe value for volumes
    -w <Gigabytes> Warning value
    -c <Gigabytes> Critical value
    -h Show this help
    """ 
def get_mount_data(mount_path, in_mounts=False):
    proc = sb.Popen(['/bin/df', '-lP'], stderr=sb.PIPE, stdout=sb.PIPE)
    df = proc.communicate()[0]
    check_error(proc, df)
    dfdict = {}
    for dataset in df.strip().split('\n'):
        if 'Filesystem' in dataset:
            continue
        pieces = dataset.split()
        # Check for DF output consistency, MUST not be more than 6 columns
        if len(pieces) > 6:
            raise RuntimeError('Could not parse DF output, more than 6 lines.')
        # Return all matched mount points
        if in_mounts:
            if any(mount_path in p for p in pieces):
                # Check for repeated mount points
                if pieces[5] in dfdict:
                    raise RuntimeError('Could not parse DF output, mount points inconsistency.')
                size = str(int(pieces[3])/1000/1000)
                dfdict[pieces[5]] = size
        # Return only one match mount point 
        else:
            mount = [p == mount_path for p in pieces]
            if True in mount:
                size = str(int(pieces[3])/1000/1000)
                dfdict[pieces[5]] = size
                break
    return dfdict

if __name__ == '__main__':
    safe = 0
    warning = 0
    critical = 0
    isunique = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:s:w:c:h:",[])
        for o, a in opts:
            if o == '-s':
                safe = int(a)
            elif o == '-U':
                isunique = True
                mount_path = a
            elif o == '-M':
                isunique = False
                mount_path = a
            elif o == '-w':
                warning = int(a)
            elif o == '-c':
                critical = int(a)
            elif o == '-h':
                usage()
                sys.exit(0)
        if 0 in [warning, critical] or if not mount_path:
            print 'UNKNOWN: warning and critical MUST not be 0. Or missing options, -M -U'
            usage()
            sys.exit(2)

        mount_data = get_mount_data(mount_path, isunique)
        if not mount_data:
            raise RuntimeError('Could not find any hsm dataset.')
            
        sizes = [int(mount_data[d]) for d in mount_data]
        secure = int(len(sizes)) * safe
        sizetotal = sum(sizes)
        sizetotal = sizetotal - secure
        if critical < warning:
            print 'UNKNOWN: Critical MUST not be lower than Warning'
            sys.exit(3)
        if sizetotal >= critical:
            print 'CRITICAL: %sGB free' % sizetotal
            sys.exit(2) 
        elif sizetotal < critical and sizetotal >= warning:
            print 'WARNING: %sGB free' % sizetotal
            sys.exit(1)
            
        print 'OK: %sGB free' % sizetotal
        sys.exit(0)
            
    except getopt.GetoptError, ex:
        usage()
        sys.exit(2)
    except Exception, e:
        print e
        sys.exit(2)
