""" Change to the hsm volume with less space
Author: Sandro Mello <sandromll@gmail.com>

It's important to configure the first volume before running this:
  $ zmvolume -a -n hsm01 -t secondaryMessage -p /opt/zimbra/hsm01
  $ zmvolume -sc -id <the id of the secondaryMessage>

Then:
  $ ./hsm_update.py

TODO: Give a proper error if there is any secondaryMessage volume configured
"""

#!/usr/bin/python
from traceback import format_exc
import subprocess as sb
import syslog
import sys

syslog.openlog('hsm-update', syslog.LOG_PID, syslog.LOG_SYSLOG)

ZIMBRA_BIN = '/opt/zimbra/bin'
ZMVOLUME = '%s/zmvolume'% ZIMBRA_BIN
ZMHSM = '%s/zmhsm'% ZIMBRA_BIN 

def check_error(proc, command):
    if proc.returncode == 1:
        raise RuntimeError('Error subprocessing command: %s' % command)
    
def zmhsm_status():
    proc = sb.Popen([ZMHSM, '--status'], stdout=sb.PIPE, stderr=sb.PIPE)
    zm = proc.communicate()[0]
    check_error(proc, zm)
    for z in zm.split('\n'):
        if 'Currently running' in z:
            syslog.syslog(syslog.LOG_INFO, 'zmhsm is running, could not start.')
            return True
            
def zmhsm_start():
    if not zmhsm_status():
        proc = sb.Popen([ZMHSM, '--start'], stdout=sb.PIPE, stderr=sb.PIPE)
        zm = proc.communicate()[0]
        check_error(proc, zm)

def define_volume(vol_id):
    proc = sb.Popen([ZMVOLUME, '-sc', '-id', vol_id], stdout=sb.PIPE, stderr=sb.PIPE)
    zmvol = proc.communicate()[0]
    check_error(proc, zmvol)
        
def get_volume_data(path):
    proc = sb.Popen([ZMVOLUME, '-l'], stdout=sb.PIPE, stderr=sb.PIPE)
    vols = proc.communicate()[0]
    check_error(proc, vols)
    voldict = {}
    for zmvol in vols.split('\n'):
        listline = zmvol.replace(' ', '').split(':')
        if len(listline) == 2:
            voldict[listline[0]] = listline[1]
        if path == voldict.get('path'):
            if not voldict.get('type') == 'secondaryMessage':
                raise RuntimeError('Volume is not secondaryMessage type!')
            return voldict
            
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
    try:
        mount_data = get_mount_data('/opt/zimbra/hsm')
            
        max_hsm = {}
        # Get the bigger value
        max_size = str(max([float(mount_data[d]) for d in mount_data]))
        for d in mount_data:
            if max_size == mount_data[d]:
                max_hsm[max_size] = d

        proc = sb.Popen([ZMVOLUME, '-dc'], stdout=sb.PIPE, stderr=sb.PIPE)
        zmvols = proc.communicate()[0]
        check_error(proc, zmvols)
        zmdict = {}
        for zmvol in zmvols.split('\n'):
            listline = zmvol.replace(' ', '').split(':')
            if len(listline) == 2:
                zmdict[listline[0]] = listline[1]
            
            # Check if it has any entries that start with /opt/zimbra/hsm in zmvol data
            if any('/opt/zimbra/hsm' in hsm for hsm in zmvol.split()):
                break
        
        if not 'hsm' in zmdict.get('path'):
            raise RuntimeError('Could not find any secondaryMessage Volume.')
            
        # Check if current volume is the same as the MAX free space volume dataset
        if zmdict['path'] == max_hsm[max_size]:
            syslog.syslog(syslog.LOG_INFO, 'Volume already set.')
            zmhsm_start()
            sys.exit(0)
        
        maxvol = get_volume_data(max_hsm[max_size])
        if not maxvol:
            raise RuntimeError('Could not find any valid volume: %s' % max_hsm[max_size])
        
        define_volume(maxvol['Volumeid'])
        syslog.syslog(syslog.LOG_INFO, 'Volume changed sucessfully to Volume: %s and ID: %s' % (maxvol['path'], maxvol['Volumeid']))
        zmhsm_start()

    except RuntimeError, re:
        syslog.syslog(syslog.LOG_ERR, 'ERROR: %s - Stack Trace: %s' % (str(e), format_exc()))
    except Exception, e:
        syslog.syslog(syslog.LOG_ERR, 'ERROR: %s - Stack Trace: %s' % (str(e), format_exc()))
    finally:
        zmhsm_start()
        sys.exit(1)
