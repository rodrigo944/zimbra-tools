# Requires: python-requests

import requests, string
from requests.auth import HTTPBasicAuth
import base64, getopt, sys
#user = 'nagios'
#passwd = 'passwd'
#host = 'r-zu2.u.inova.com.br'
#dev_id = 'Appl881156DPA4S'
#dev_type = 'IPhone'

def activesync(user, passwd, host, dev_id, dev_type='IPhone'):
  try:
    user = user.split('@')[0]
    headers = { 'Host' : host,
      'Expect' : '100-continue',
      'MS-ASProtocolVersion' : '12.0',
      'Connection' : 'Keep-Alive',
      'User-Agent' : dev_type,
      'Content-Type' : 'application/vnd.ms-sync.wbxml'
    }
    auth = HTTPBasicAuth('%s\%s' % (host,user), passwd)
    req_address = 'https://%s/Microsoft-Server-ActiveSync?Cmd=FolderSync&User=%s&DeviceId=%s&DeviceType=%s' % (host, user, dev_id, dev_type)
    req = requests.post(url=req_address, headers=headers, auth=auth, verify=False)
    # Remove unpritable characters from string
    response = filter(lambda x: x in string.printable, req.text)
    if 'Inbox' in response:
      print 'ActiveSync is working | ActiveSync=2'
      sys.exit(0)
    else:
      print 'ActiveSync is NOT working | ActiveSync=0'
      sys.exit(2)

  except Exception, e:
    print '%s | ActiveSync=0' % e
    sys.exit(2)

def webmail(server, user, password):
    soapEnvelope = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header>\
<context xmlns="urn:zimbra"><nosession/></context></soap:Header><soap:Body><AuthRequest xmlns="urn:zimbraAccount">\
<account by="name">%s</account><password>%s</password></AuthRequest></soap:Body>\
</soap:Envelope>""" % (user, password)
    headers = {
      'Content-Type' : 'text/soap+xml'
    }
    zimbraUrl = 'http://%s/service/soap/AuthRequest' % server
    try:
      req = requests.post(url=zimbraUrl, headers=headers, data=soapEnvelope)
      if req.status_code == 200:
        print 'Logged in server: %s. account: %s | WEBMAIL=2' % (server, user)
        sys.exit(0)
      else:
        print 'Wrong credentials in server: %s. account: %s | WEBMAIL=0' % (server, user)
        sys.exit(2)
    except requests.exceptions.ConnectionError, e:
      print e
      sys.exit(2)

def usage():
    print """ActiveSync/Webmail Authentication
    -s <server> Server name (required)
    -u <login> Login name <user@domain> (required)
    -p <password> Login password (required)
    --activesync do activesync check
    --webmail do webmail check
    --devid device id to test (required for activesync check)
    --devtype name of the device type. E.g.: IPhone (required for activesync check)
    -h Show this help
    """ 
    sys.exit(2)

if __name__ == '__main__':
  try:
    opts, args = getopt.getopt(sys.argv[1:], "s:u:p:h:", ['activesync', 'webmail', 'devid=', 'devtype='])
  except getopt.GetoptError, ex:
    print ex
    usage()
    sys.exit(3)
    
  runcheck = None
  username = server = password = None
  dev_id = dev_type = None

  for i in opts:
    if i[0] == '--devid':
      dev_id = i[1]
    elif i[0] ==  '--devtype':
      dev_type = i[1]
    elif i[0] == '-s':
      server = i[1]
    elif i[0] == '-u':
      username = i[1]
    elif i[0] == '-p':
      password = i[1]
    elif i[0] == '--activesync':
      runcheck = i[0]
    elif i[0] == '--webmail':
      runcheck = i[0]
    elif i[0] == '-h':
      usage()
    else:
      print 'Wrong args'
      usage()

  if runcheck == '--activesync':
    if True in [param == None for param in [username, server, password, dev_id, dev_type]]:
      print 'missing parameters'
      usage()
    else:
      activesync(username, password, server, dev_id, dev_type)
  elif runcheck == '--webmail':
    if True in [param == None for param in [username, server, password]]:
      print 'missing parameters'
      usage()
    else:
      webmail(server, username, password)
  else:
    print 'Must specify --activesync or --webmail'
    usage()
