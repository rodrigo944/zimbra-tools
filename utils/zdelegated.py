#!/usr/bin/python
from zrequests import ZimbraRequest, ZimbraRequestError
from collections import namedtuple
import sys, argparse, getpass
from traceback import format_exc

ZIMBRA_GRANTS = [
  'domainAdminConsoleRights',
  'getDomainQuotaUsage',
  'get.domain.zimbraDomainCOSMaxAccounts',
  'countAccount',
  'set.account.zimbraCOSId',
  'viewAdminConsoleDomainInfoTab',
  'addDistributionListMember'
]

DLIST_PROPERTIES = {
  'zimbraAdminConsoleUIComponents' : [
      'accountListView',
      'COSListView',
      'DListView',
      'resourceListView',
      'aliasListView',
      'DLListView',
      'domainListView'
    ],
  'zimbraMailStatus': 'disabled',
  'zimbraIsAdminGroup': 'TRUE',
  'zimbraHideInGal': 'TRUE',
  'description': 'Grupo com Rights de visualizacao do COS professional'
}

class ZimbraGrants:
  def __init__(self, target_name, target_dlist):
    self.target_name = target_name
    self.target_dlist = target_dlist

    ZGrant = namedtuple(
      'ZimbraGrant', [ 
        'target_name', 
        'target_type', 
        'grantee_name',
        'grantee_type', 
        'right', 
        'deny'
      ]
    )
    
    self.result_grants = []
    for zgrant in ZIMBRA_GRANTS:
      self.result_grants.append(
        ZGrant(
          target_name = self.target_name,
          target_type = 'domain',
          grantee_name = self.target_dlist,
          grantee_type = 'grp',
          right = zgrant,
          deny = 0
        )
      )

  def __iter__(self):
    return self

  def next(self):
    if not self.result_grants:
      raise StopIteration
    return self.result_grants.pop()

class ZDelegated(object):
  def __init__(self, service_api, global_admin_user, global_admin_passwd, target_user, dlist_name, append = False):
    self.admin_user = global_admin_user
    self.admin_passwd = global_admin_passwd
    self.service_api = service_api
    self.dlist_name = dlist_name
    self.zdelegated_admin_account = target_user
    self.append = append

  def start(self):
    dlist_zimbra_id = None
    try:
      zr = ZimbraRequest(
        admin_url = 'https://%s:7071/service/admin/soap' % self.service_api, 
        admin_user = self.admin_user, 
        admin_pass = self.admin_passwd
      )
      print 'Creating distribution list %s...' %  self.dlist_name
      response = zr.createDistributionList(self.dlist_name, DLIST_PROPERTIES.items())
      dlist_zimbra_id = response['CreateDistributionListResponse']['dl']['id']
      if not dlist_zimbra_id:
        raise ValueError('dlist_zimbra_id must not be empty. Should not get here!')
    except ZimbraRequestError, e:
      if e.response.get_fault_code() == 'account.DISTRIBUTION_LIST_EXISTS':
        print 'DL', self.dlist_name, 'already exists!'
      else:
        print 'Unkwnon Error'
        raise

    try:
      print 'Configuring GRANTS...'
      domain_name = self.zdelegated_admin_account.split('@')[1]
      for zgrant in ZimbraGrants(domain_name, self.dlist_name):
        print 'target_name: %s target_type: %s grantee_name: %s grantee_type: %s right: %s' % \
         (zgrant.target_name, zgrant.target_type, zgrant.grantee_name, zgrant.grantee_type, zgrant.right)
        zr.grantRight(
          target_name = zgrant.target_name,
          target_type = zgrant.target_type,
          grantee_name = zgrant.grantee_name,
          grantee_type = zgrant.grantee_type,
          right = zgrant.right,
        )
      print 'Grants applied successfully!'

      if not self.append:
        response = zr.createAccount(self.zdelegated_admin_account, attrs = [('zimbraIsDelegatedAdminAccount', 'TRUE')])

    except ZimbraRequestError, e:
      if e.response.get_fault_code() == 'account.ACCOUNT_EXISTS':
        # Account exists, should be an admin account
        print 'Account %s already exists' % self.zdelegated_admin_account
        # TODO: Should not get here. Deal with that later
      raise

    # If the create process failed, the list exists. We need get the dlist ID
    if not dlist_zimbra_id:
      print 'Adding user %s to the distribution list %s' % (self.zdelegated_admin_account, self.dlist_name)
      response = zr.getDistributionList(self.dlist_name)
      dlist_zimbra_id = response['GetDistributionListResponse']['dl']['id']

    zr.addDistributionListMember(dlist_zimbra_id, [self.zdelegated_admin_account])

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Zimbra Delegated Admin Cli')
  parser.add_argument('-a', help='The target account to grant rights', required = True)
  parser.add_argument('-s', metavar="<ip/hostname>", help='The target server API. Tries to connect with port 7071', required = True)
  parser.add_argument('--admin', help='Zimbra global admin account', required = True)
  parser.add_argument('--dlist', help='The name of the distribution list permission', required = True)
  parser.add_argument('--append', action='store_true', help='Append the target account to distribution list')
  parser.add_argument('--grants', metavar='<grant01,grant02,...>', help='Additional grants')
  parser.add_argument('--debug', action='store_true', help='Turn on debuging')
  args = parser.parse_args()

  if args.grants:
    for zgrant in args.grants.split(','):
      ZIMBRA_GRANTS.append(zgrant)  

  passwd = getpass.getpass('GLOBAL ADMIN: %s password:\n' % args.admin)

  zd = ZDelegated(
    service_api = args.s, 
    global_admin_user = args.admin, 
    global_admin_passwd = passwd,
    target_user = args.a,
    dlist_name = args.dlist,
    append = args.append
  )
  try:
    zd.start()
  except Exception, e:
    print e
    if args.debug:
      print format_exc()
    sys.exit(1)