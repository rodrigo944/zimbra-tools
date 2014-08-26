""" Provisioning functions Zimbra to Zimbra given ldap entries. 
Requires: python-ldap
Author: Sandro Mello <sandromll@gmail.com>
"""
import ldap, sys, re
import xml.etree.ElementTree as ET
import datetime
import itertools, httplib, ssl, urllib2, socket

# NOTE: Using imapsync, put the following regex to remove unrecognized flags --regexflag 's/:FLAG.*//g'

""" Tag Colors Zimbra - From 8.0.7
<tag id="41995" color="9" name="orange"/>
<tag id="41990" color="4" name="purple"/>
<tag id="41989" color="3" name="green"/>
<tag id="41992" color="6" name="yellow"/>
<tag id="41994" color="8" name="gray"/>
<tag id="41986" color="2" name="cyan"/>
<tag id="41991" color="5" name="red"/>
<tag id="41988" color="1" name="blue"/>
<tag id="41993" color="7" name="pink"/>
"""

TAG_COLORS = {
  '1' : 'blue',
  '2' : 'cyan',
  '3' : 'green',
  '4' : 'purple',
  '5' : 'red',
  '6' : 'yellow',
  '7' : 'pink',
  '8' : 'gray',
  '9' : 'orange'
}

#Redhat eliptic curve ssl bug:
#https://eucalyptus.atlassian.net/browse/EUCA-8317
class HTTPSConnectionV3(httplib.HTTPSConnection):
  def __init__(self, *args, **kwargs):
    httplib.HTTPSConnection.__init__(self, *args, **kwargs)

  def connect(self):
    sock = socket.create_connection((self.host, self.port), self.timeout)
    if self._tunnel_host:
      self.sock = sock
      self._tunnel()
    try:
      self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv3)
    except ssl.SSLError, e:
      print("Trying SSLv3.")
      self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)

class HTTPSHandlerV3(urllib2.HTTPSHandler):
  def https_open(self, req):
    return self.do_open(HTTPSConnectionV3, req)

LOCALCONFIG = 'localconfig.xml'
URL_API = 'https://192.168.6.78:7071/service/admin/soap'

class ZimbraRequest(object):
  def __init__(self, source_cred, account):
    self.req_headers = { 'Content-Type': 'application/soap+xml' }
    urllib2.install_opener(urllib2.build_opener(HTTPSHandlerV3()))
    self.url_api = URL_API
    self.admin_src_user = source_cred['zimbra_user']
    self.admin_src_password = source_cred['zimbra_ldap_password']
 
    try:
      self.src_token = self.get_token(self.token_xml(self.admin_src_user, self.admin_src_password))
      self.delegated_src_token = self.get_token(self.delegate_token_xml(account, self.src_token))
    except urllib2.URLError, e:
      raise Exception('Error getting tokens, check the credentials. %s' % e)

  def get_token(self, token_xml):
    req = urllib2.Request(URL_API, token_xml, self.req_headers)
    resp = urllib2.urlopen(req)
    root = ET.fromstring(resp.read())
    token = root.find('.//{urn:zimbraAdmin}authToken').text
    return token

  def delegate_token_xml(self, account, token):
    return '<?xml version="1.0" ?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra">\
<authToken>%s</authToken></context></soap:Header><soap:Body><DelegateAuthRequest duration="86400" xmlns="urn:zimbraAdmin">\
<account by="name">%s</account></DelegateAuthRequest></soap:Body></soap:Envelope>' % (token, account)

  def token_xml(self, admin_user, admin_password):
    return '<?xml version="1.0" ?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">\
<soap:Header><context xmlns="urn:zimbra"><format type="xml"/></context></soap:Header><soap:Body><AuthRequest xmlns="urn:zimbraAdmin">\
<name>%s</name><password>%s</password></AuthRequest></soap:Body></soap:Envelope>' % (admin_user, admin_password)

  def get_info_request(self, account, token):
    return '<?xml version="1.0" ?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">\
<soap:Header><context xmlns="urn:zimbra"><authToken>%s</authToken><session/><account by="name">%s</account><userAgent name="zclient" version="8.0.7_GA_6020"/></context></soap:Header>\
<soap:Body><GetInfoRequest sections="mbox,prefs,attrs,props,idents,sigs,dsrcs,children" rights="" xmlns="urn:zimbraAccount"/>\
</soap:Body></soap:Envelope>' % (token, account)

  def create_tag_request_xml(self, token, account, tag_metadata):
    tag_xml = None
    for md in tag_metadata:
      tag_xml += '<tag color="%s" name="%s"/>' % ( md['color'], md['name'] )
    return '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header><context xmlns="urn:zimbra">\
  <authToken>%s</authToken><account by="name">%s</account>\
  <userAgent name="zclient" version="8.0.7_GA_6020"/></context></soap:Header><soap:Body><CreateTagRequest xmlns="urn:zimbraMail">\
  %s</CreateTagRequest></soap:Body></soap:Envelope>' % (token, account, tag_xml)

  def get_tags(self, account):
    delegated_token = self.get_token(self.delegate_token_xml(account, self.src_token))
    soap_request = self.get_info_request(account, delegated_token)
    #print self.delegate_token_xml(account)
    req = urllib2.Request(self.url_api, soap_request, self.req_headers)
    resp = urllib2.urlopen(req)
    
    root = ET.fromstring(resp.read())
    #self.sessionid = root.find('.//{urn:zimbra}session')
    account_tags = []
    for tags in root.findall('.//{urn:zimbra}tags'):
      [account_tags.append(tag.attrib) for tag in tags.findall(".//{urn:zimbra}tag")]
    return account_tags

  #def set_tags(self, account, tag_metadata):
  #  soap_request = self.create_tag_request_xml(self.delegated_dest_token, account, tag_metadata)
  #  req = urllib2.Request(self.ur, soap_request, self.req_headers)
  #  resp = urllib2.urlopen(req)
     #root = ET.fromstring(resp.read())
  #  return resp.read()


def getLdapCredentials():
  """ Get Ldap credentials from Zimbra config file: localconfig.xml
  Expected output: {'zimbra_ldap_password': '<passwd>', 'ldap_url': '<ldap_uri>', 'zimbra_ldap_userdn': '<userdn>'} """
  tree = ET.parse(LOCALCONFIG)
  root = tree.getroot()
  
  ldap_data = dict()
  try:
    for key in root.findall('key'):
      if key.attrib['name'] in ['ldap_url', 'zimbra_ldap_password', 'zimbra_ldap_userdn', 'zimbra_user']:
        ldap_data[key.attrib['name']] = key.find('value').text

  except AttributeError, ex:
    print 'Error getting ldap credentials in %s: %s ' % (LOCALCONFIG, ex)
    sys.exit(1)
  if not ldap_data:
    print 'Ldap credentials empty'
    sys.exit(1)

  return ldap_data

def ldapQuery(ldp_conf, query, attrs):
  """ Search in the ldap directory
  :param ldp_conf: Dict with the following format - {'zimbra_ldap_password': '<passwd>', 'ldap_url': '<ldap_uri>', 'zimbra_ldap_userdn': '<userdn>'}
  :param query: Str containing the ldap query. Example: (&(objectClass=zimbraDistributionList))
  :param attrs: List containing the attributes to return """
  try:
    ldp = ldap.initialize(ldp_conf['ldap_url'])
    ldp.simple_bind_s(ldp_conf['zimbra_ldap_userdn'], ldp_conf['zimbra_ldap_password'])
    return ldp.search_s('', ldap.SCOPE_SUBTREE, query, attrs)
  except Exception, e:
    print 'Error querying to ldap, data: %s query: %s Error: %s' % (e, ldp_conf, query)
    sys.exit(1)

def getCosByName(cred):
  # { 'cosname' : 'zimbraId', ... }
  query = '(objectClass=zimbraCOS)'
  attrs = ['zimbraId']
  r = {}
  for dn, entry in ldapQuery(cred, query, attrs):
    try:
      cos = dn.split('cn=')[1]
      r[cos] = entry['zimbraId'][0]
    except KeyError, e:
      print "Error Key %s" % e
      sys.exit(1)
  return r

def compareByZimbraTimestamp():
  result = ''
  # Here we get only the entrys of the response. Expected: {'zimbraMailForwardingAddress': ['financeiro@hv.tur.br'], 'mail': ['adm@hv.tur.br']}
  for dn, entry in ldapQuery(cred, query, attrs):
    try:
      zimbraCreateTimestamp = convert_iso8601(entry['zimbraCreateTimestamp'][0])
      # 2013/Novembro/10 00hs
      fromtime = convert_iso8601('20131110000000Z')
      #print zimbraCreateTimestamp > fromtime
      if zimbraCreateTimestamp > fromtime:
        print entry['zimbraMailDeliveryAddress'][0]
    except KeyError:
      pass

def convert_iso8601(datestr):
  # E.g.: ISO8601 format: 20131011000000Z (ANO/DIA/MES/HORA/MINUTO/SEGUNDO|FUSO)
  return datetime.datetime.strptime(datestr, '%Y%m%d%H%M%SZ')

def zimbra_attributes():
  """ We use this attributes for provisioning each zimbra account. It's easy to migrate
  static attributes from accounts like signatures, filters, etc.
  Note: Be careful with different zimbra version, some attributes may not be in the new version
  """
  return [ 'zimbraPrefPop3DownloadSince' ]

def prov_account(ldp_cnf, ldap_query, attrs):
  """ Print the string for provisioning accounts according to the query.    
  :param ldp_conf: Dict with the following format - {'zimbra_ldap_password': '<passwd>', 'ldap_url': '<ldap_uri>', 'zimbra_ldap_userdn': '<userdn>'}
  :param ldap_query: Str containing the ldap query. Example: (&(objectClass=zimbraDistributionList))
  :param attrs: List containing the attributes to return
  """
  acc = open('contas/15days/15_days_logon2').read().strip().split('\n')
  for dn, entry in ldapQuery(ldp_cnf, ldap_query, attrs):
    mail_account = entry['zimbraMailDeliveryAddress'][0]
    if mail_account in acc:
      continue
    print mail_account
    #print mail_account

def provDistributionList(ldp_conf, ldap_query, attrs):
  """ Print the string for provisioning distribution lists according to the query.
  :param ldp_conf: Dict with the following format - {'zimbra_ldap_password': '<passwd>', 'ldap_url': '<ldap_uri>', 'zimbra_ldap_userdn': '<userdn>'}
  :param ldap_query: Str containing the ldap query. Example: (&(objectClass=zimbraDistributionList))
  :param attrs: List containing the attributes to return
  """
  for dn, entry in ldapQuery(ldp_conf, ldap_query, attrs):
    distribution_list_name = entry['mail'][0]
    print 'createDistributionList', distribution_list_name
    print 'addDistributionListMember', distribution_list_name, 
    for member in entry['zimbraMailForwardingAddress']:
      print member,
    # Break line, distribution list member finished
    print
  # Finish
  print

def prov_tags(account, tags_metadata, action='create'):
  for tag in tags_metadata:
    color_number = tag.get('color')
    if not color_number:
      # If has a custom color, set it to orange
      color_number = '9'
    color_name = TAG_COLORS[color_number]
    # Remove whitespaces from string
    tag_name = re.sub('\s', '_', tag['name'])
    # Remove accents
    if type(tag_name) is unicode:
      tag_name = tag_name.encode('ascii', 'ignore')
    #tag_name = unicode(tag_name, 'UTF-8').encode('ASCII', 'ignore')
    if action == 'create':
      print "sm %s createTag --color %s %s" % (account, color_name, tag_name)
    else:
      print "sm %s deleteTag %s" % (account, tag_name)


def get_zimbra_accounts(ldp_cnf, ldap_query, attrs):
  accounts = []
  for dn, entry in ldapQuery(ldp_cnf, ldap_query, attrs):
    mail_account = entry['zimbraMailDeliveryAddress'][0]
    accounts.append(mail_account)
  return accounts

if __name__ == '__main__':
  source_cred = getLdapCredentials()
  query = '(&(objectClass=zimbraAccount)(!(zimbraIsSystemResource=TRUE))(!(objectClass=zimbraCalendarResource)))'
  attrs = ['zimbraPrefPop3DownloadSince', 'zimbraMailDeliveryAddress']
  attrs = []

  """ Redirect the output to a specified file, then you can run:
  $ zmprov -f provisioning.zm 
  """

  ### Account Provisioning ###
  #prov_account(source_cred, query, attrs)
  
  ### Tag Provisioning ###
  accounts = get_zimbra_accounts(source_cred, query, attrs)

  
  for zaccount in accounts:
    zr = ZimbraRequest(source_cred, zaccount)
    # Output example: [{'rgb': '#FFFFFF', 'id': '190731', 'name': 'DELL', 'n': '5'}, {'color': '5', 'u': '3', 'id': '2430', 'name': 'importante', 'n': '151'}, ...
    tags_metadata = zr.get_tags(zaccount)  
    prov_tags(zaccount, tags_metadata)

  ### Distribution LIST Provisioning ###
  #query = '(&(objectClass=zimbraDistributionList))'
  #provDistributionList(cred, query, attrs)

  # { 'cosname' : 'zimbraId', ... }

  #sm admin@lab01.u.inova.com.br createTag -c blue inova
