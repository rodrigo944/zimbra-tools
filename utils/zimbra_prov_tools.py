""" Provisioning functions Zimbra to Zimbra given ldap entries. 
Requires: python-ldap
Author: Sandro Mello <sandromll@gmail.com>
"""
import ldap, sys
import xml.etree.ElementTree as ET
import datetime

LOCALCONFIG = '/opt/zimbra/conf/localconfig.xml'

def getLdapCredentials():
  """ Get Ldap credentials from Zimbra config file: localconfig.xml
  Expected output: {'zimbra_ldap_password': '<passwd>', 'ldap_url': '<ldap_uri>', 'zimbra_ldap_userdn': '<userdn>'} """
  tree = ET.parse(LOCALCONFIG)
  root = tree.getroot()
  
  ldap_data = dict()
  try:
    for key in root.findall('key'):
      if key.attrib['name'] in ['ldap_url', 'zimbra_ldap_password', 'zimbra_ldap_userdn']:
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
      # 2013/Novembro/10:00hs
      fromtime = convert_iso8601('20131110000000Z')
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
  return [ 'displayName',
  'zimbraAccountstatus',
  'givenName',
  'sn',
  'zimbraIsAdminAccount',
  'zimbraPrefMailForwardingAddress',
  'zimbraPrefOutOfOfficeCacheDuration',
  'zimbraPrefOutOfOfficeDirectAddress',
  'zimbraPrefOutOfOfficeFromDate',
  'zimbraPrefOutOfOfficeReply',
  'zimbraPrefOutOfOfficeReplyEnabled',
  'zimbraPrefOutOfOfficeUntilDate',
  'zimbraPrefHtmlEditorDefaultFontColor',
  'zimbraPrefHtmlEditorDefaultFontFamily',
  'zimbraPrefHtmlEditorDefaultFontSize',
  'zimbraPrefMessageViewHtmlPreferred',
  'zimbraMailSieveScript',
  'zimbraPrefComposeFormat',
  'zimbraPrefGroupMailBy',
  'zimbraSignatureName',
  'zimbraSignatureId',
  'zimbraPrefMailSignatureHTML',
  'zimbraPrefMailSignature',
  'zimbraPrefForwardReplySignatureId',
  'zimbraPrefDefaultSignatureId',
  'userPassword' ]

def prov_account(ldp_cnf, ldap_query, attrs):
  """ Print the string for provisioning accounts according to the query.    
  :param ldp_conf: Dict with the following format - {'zimbra_ldap_password': '<passwd>', 'ldap_url': '<ldap_uri>', 'zimbra_ldap_userdn': '<userdn>'}
  :param ldap_query: Str containing the ldap query. Example: (&(objectClass=zimbraDistributionList))
  :param attrs: List containing the attributes to return
  """
  for dn, entry in ldapQuery(ldp_cnf, ldap_query, attrs):
    mail_account = entry['zimbraMailDeliveryAddress'][0]
    print 'createAccount %s pwBeijinhoNoOmbro' % mail_account,
    for zimbra_attr in zimbra_attributes():
      try:
        attr_data = entry[zimbra_attr]
        print zimbra_attr,
        for value in attr_data:
          # We need to print \n instead of breaking line.
          value = value.replace('\n', '\\n')
          # We need to escape single quotes.
          value = value.replace("'", "\\'")
          if zimbra_attr == 'zimbraPrefMailForwardingAddress':
            # zimbraPrefMailForwardingAddress must always have accounts separated by comma
            value = value.replace(';', ',')

          print "'%s'" % value,
      except KeyError:
          continue
    
    # Attributes finished for the given account, we need to break line to move to next account
    print

    if entry.get('zimbraMailAlias'):
      for alias in entry['zimbraMailAlias']:
        print 'addAccountAlias', mail_account, alias

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
    if not 'zimbraMailForwardingAddress' in entry:
      continue
    for member in entry['zimbraMailForwardingAddress']:
      print member,
    # Break line, distribution list member finished
    print
  # Finish
  print

if __name__ == '__main__':
  cred = getLdapCredentials()
  query = '(&(objectClass=zimbraAccount)(!(zimbraIsSystemResource=TRUE))(!(objectClass=zimbraCalendarResource)))'
  #attrs = ['zimbraMailDeliveryAddress']
  attrs = []

  """ Redirect the output to a specified file, then you can run:
  $ zmprov -f provisioning.zm 
  """
  prov_account(cred, query, attrs)

  query = '(&(objectClass=zimbraDistributionList))'
  provDistributionList(cred, query, attrs)

  # { 'cosname' : 'zimbraId', ... }
  #cos = getCosByName(cred)
  
