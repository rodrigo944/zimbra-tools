#!/usr/bin/python
import getopt
import subprocess as sb
import sys

def check_error(proc, command):
    if proc.returncode == 1:
        raise RuntimeError('Error subprocessing command: %s' % command)
        
def usage():
    print """Check free space volumes from /bin/df
    -s <Gigabytes> Safe value for volumes
    -w <Gigabytes> Warning value
    -c <Gigabytes> Critical value
    -U <Gigabytes> Unique mount point
    -M <Gigabytes> Multiple mount points
    -m <Warning_Gigabytes:Critical_Gigabytes> Single max space volume 
    -h Show this help

    * EXAMPLES
    check_volumes -w 150 -c 100 -m 70:60 -U /
    --------------------------------
    Values equal or above 60GB will lead to a CRITICAL state, between 70GB and 61GB will lead to a WARNING state,  Values from 150GB ~ 101GB will lead to a WARNING state. Values less or equal to 100GB will lead to a CRITICAL state.
    Above 150GB will lead to an 'OK' state. -U check for unique volumes, on this case: / Mount point

    check_volumes -w 200 -c 120 -M hsm
    ----------------------------------
    Values from 200GB ~ 121GB will lead to a WARNING state. Values less or equal 120GB will lead to a CRITICAL state.
    Above 200GB will lead to an 'OK' state. -M on this case matches all the volumes that contains the string 'hsm' and sum
    the free space available on those disks.
    /opt/zimbra/hsm01, /opt/zimbra/hsm02 and /opt/zimbra/hsm3 will match;
    /var/hsm/sasl, /var/hsm/store will match.
    The string will match with the volumes in the sixth column of /bin/df command 
    """ 
    
import subprocess as sb

def join_pieces(mount_path, size, dfdict):
    f = float(size)/1024/1024
    size = str('%.1f' %f)
    dfdict[mount_path] = size

def get_mount_data(mount_path, uniq=False):
    proc = sb.Popen(['/bin/df', '-P'], stderr=sb.PIPE, stdout=sb.PIPE)
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
        if not uniq:
            if any(mount_path in pieces[5] for p in pieces):
                # Check for repeated mount points
                if pieces[5] in dfdict:
                    raise RuntimeError('Could not parse DF output, mount points inconsistency.')
                join_pieces(pieces[5], pieces[3], dfdict)
                
        # Return only one match mount point 
        else:
            mount = [p == mount_path for p in pieces]
            if True in mount:
                join_pieces(pieces[5], pieces[3], dfdict)
                break
    return dfdict

if __name__ == '__main__':
    warning = critical = warning_max = critical_max = 0
    isunique = mount_path = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:U:M:w:c:h:")
        for o, a in opts:
            if o == '-U':
                isunique = True
                mount_path = a
            elif o == '-M':
                isunique = False
                mount_path = a
            elif o == '-w':
                warning = int(a)
            elif o == '-c':
                critical = int(a)
            elif o == '-m':
                try:
                    inp = a.split(':')
                    warning_max = int(inp[0])
                    critical_max = int(inp[1])
                except IndexError:
                    raise
            elif o == '-h':
                usage()
                sys.exit(0)
            else:
                print 'UNKNOWN: Wrong option'
                usage()
                sys.exit(3)
                
        if 0 in [warning, critical]:
            print 'UNKNOWN: warning and critical MUST not be 0.'
            usage()
            sys.exit(3)
        if not mount_path:
            print 'UNKNOWN: Missing -U or -M parameter'
            usage()
            sys.exit(3)
        mount_data = get_mount_data(mount_path, isunique)
        if not mount_data:
            raise RuntimeError('Could not find any Volumes.')
            
        sizes = [float(mount_data[d]) for d in mount_data]
        max_size = max(sizes)
        sizetotal = sum(sizes)
        
        if not isunique:
            max_total = {}
            for key in mount_data:
                if str(max_size) == mount_data[key]:
                    max_total[str(max_size)] = key
                    
            max_msg = {}
            if warning_max < critical_max:
                print 'UNKNOWN: WARNING_MAX MUST NOT be lower than CRITICAL_MAX.'
                sys.exit(3)
            elif max_size <= critical_max:
                max_msg = ['2', 'CRITICAL: Volume %s. %sGB free' % ( max_total[str(max_size)], max_size )]
            elif max_size <= warning_max:
                max_msg = ['1', 'WARNING: Volume %s. %sGB free' % ( max_total[str(max_size)], max_size )]
        
        if warning < critical:
            print 'UNKNOWN: WARNING MUST NOT be lower than CRITICAL.'
            sys.exit(3)
        elif sizetotal <= critical:
            print 'CRITICAL: Total of %sGB free' % sizetotal
            sys.exit(2) 
        elif sizetotal <= warning:
            print 'WARNING: Total of %sGB free' % sizetotal
            sys.exit(1)
        if max_msg:
            print max_msg[1]
            sys.exit(int(max_msg[0]))
                
        print 'OK: %sGB free' % sizetotal
        sys.exit(0)
            
    except getopt.GetoptError, ex:
        usage()
        sys.exit(2)
    except Exception, e:
        print 'UNKNOWN: %s' % e
        sys.exit(3)
