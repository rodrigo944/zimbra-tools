from pythonzimbra.request_json import RequestJson
from pythonzimbra.communication import Communication
from pythonzimbra.request_xml import RequestXml
from pythonzimbra.tools.dict import get_value
from pythonzimbra.tools.auth import authenticate
import json, time, hmac, hashlib, uuid

class ZimbraRequestError(Exception):
  def __init__(self, message, response=None):
    """ Request Errors Zimbra
    :param message: Error message
    :param response: pythonzimbra.response.Response type
    """
    self.message = message
    self.response = response

    super(ZimbraRequestError, self).__init__(message)

class ZimbraRequest(object):
  def __init__(self, admin_url, admin_user, admin_pass):
    self.admin_url = admin_url
    self.admin_user = admin_user
    self.admin_pass = admin_pass
    self.admin_account_by = 'name'
    self.request = None

    self.token = authenticate(
      self.admin_url, 
      self.admin_user,
      self.admin_pass,
      self.admin_account_by,
      admin_auth=True,
      request_type="json"
    )

    self.comm = Communication(self.admin_url)

  def getAllAdminAccounts(self, domain_name):
    self.cleanUp()
    self.request.add_request(
      request_name = 'GetAllAccountsRequest',
      request_dict = { 
        "domain": {
          "_content" : domain_name,
          "by": "name",
        },
        "a" : {
          "n" : "zimbraIsAdminAccount",
          "_content" : "TRUE"
        }
      },
      namespace = 'urn:zimbraAdmin'
    )

    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error getting all admin accounts. Error: %s' % response.get_fault_message(), 
        response = response
      )

    return response.get_response()

  def createDomain(self, domain_name, attrs=list()):
    """ Create a new domain
    :param domain_name: The name of the domain
    :param attrs: List of tuple attributes of domain (zmprov desc domain)
    """
    if not type(attrs) == list:
      raise TypeError('attrs must be a list')
    self.cleanUp()

    request_attrs = []
    for attr in attrs:
      zattr, value = attr
      request_attrs.append({
        'n' : zattr,
        '_content' : value
      })

    request_dict = { 'name' : domain_name }
    if request_attrs:
      request_dict['a'] = request_attrs

    self.request.add_request(
      request_name = 'CreateDomainRequest',
      request_dict = request_dict,
      namespace = 'urn:zimbraAdmin'
    )

    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error creating domain %s Error: %s' % (domain_name, response.get_fault_message()), 
        response = response
      )

    return response.get_response()

  def deleteDomain(self, domain_id):
    """ Delete a domain
    :param domain_id: The zimbraId of the domain
    """
    self.cleanUp()

    self.request.add_request(
      request_name = 'DeleteDomainRequest',
      request_dict = { 'id' : domain_id },
      namespace = 'urn:zimbraAdmin'
    )

    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error deleting domain %s Error: %s' % (domain_id, response.get_fault_message()), 
        response = response
      )

    return response.get_response()

  def getDomain(self, domain, attrs):
    """
    TODO
      - Implement list of attributes to get.
      - Raise exception when an error occours.
    """
    
    """
    Returns the attributes requested in a json format.
     "GetDomainResponse": {
      "domain": {
        "a": [
      {
         "_content": "externalLdapAutoComplete",
         "n": "zimbraGalAutoCompleteLdapFilter"
      },
      {
         "_content": "FALSE",
         "n": "zimbraAdminConsoleDNSCheckEnabled"
      },
      .
      .
      .
      https://files.zimbra.com/docs/soap_api/8.6.0/api-reference/zimbraAdmin/GetDomain.html
    """
    if not type(attrs) == list:
      raise TypeError('attrs must be a list')
    self.cleanUp()

    attrs =  ','.join(attrs)
    self.request.add_request(
      request_name = "GetDomainRequest",
      request_dict = {
        "attrs" : attrs,
        "domain": {
          "_content" : domain,
          "by": "name",
        },
      },
      namespace = "urn:zimbraAdmin"
    )
    
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error getting domain %s Error: %s' % (domain, response.get_fault_message()), 
        response = response
      )
    
    return response.get_response()
    
  def modifyDomain(self, domain_id, attrs):
    """ Modify an attribute of a domain
    This method is idempotent, it will not change the result executing multiple times
    :param domain_id: The zimbraID of the domain
    :param attrs: A list of tuple containing the zimbra attribute with the corresponding value: [(zattr, value), ...]    
    """
    self.cleanUp()

    request_attrs = []
    for attr in attrs:
      zattr, value = attr
      request_attrs.append({
        'n' : zattr,
        '_content' : value
      })

    self.request.add_request(
      request_name = "ModifyDomainRequest",
      request_dict = {
        "id": {
          "_content": domain_id,
        },
        "a": request_attrs
      },
      namespace = "urn:zimbraAdmin"
    )
    
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error modifying domain %s Error: %s' % (domain_id, response.get_fault_message()), 
        response = response
      )
    
    return response.get_response()

  def getAccount(self, account, attrs):
    """
    TODO
      - Implement a list of attributes to get.
      - Implement raise exception.
    """
    
    
    """
    Returns a json containing all attributes of an account or an exception:
    
    "GetAccountResponse": {
      "account": {
   "a": [
    {
       "_content": "FALSE",
       "n": "zimbraPrefCalendarReminderMobile"
    },
          {
        "_content": "TRUE",
        "n": "zimbraPrefIMLogChats"
    },
    .
    .
    .
    
    https://files.zimbra.com/docs/soap_api/8.6.0/api-reference/zimbraAdmin/GetAccount.html
    """
    if not type(attrs) == list:
      raise TypeError('attrs must be a list')

    attrs =  ','.join(attrs)
    self.cleanUp()
    
    self.request.add_request(
      "GetAccountRequest",
      {
        "attrs" : attrs,
        "account": {
          "_content": account,
          "by": "name",
        },
      },
      "urn:zimbraAdmin"
    )
    
    response = self.comm.send_request(self.request)
    
    if response.is_fault():
      raise ZimbraRequestError("Reponse failed: (%s) %s" % (response.get_fault_code(), response.get_fault_message()))
    return(response.get_response())

  def createAccount(self, account, password=None, attrs=list()):
    """ Create a new account into Zimbra system
    :param account: The target account
    :param password: The given for the account
    :param attrs: A list of tuple containing the zimbra attribute with the corresponding value: [(zattr, value), ...]
    """
    request_attrs = []
    for attr in attrs:
      zattr, value = attr
      request_attrs.append({
        'n' : zattr,
        '_content' : value
      })
    
    self.cleanUp()

    if not password:
      password = hmac.new(str(uuid.uuid4), str(uuid.uuid4()), hashlib.md5).hexdigest()
    
    self.request.add_request(
      request_name = "CreateAccountRequest",
      request_dict = {
        "name" : account,
        "password" : password,
        "a" : request_attrs
      },
      namespace = "urn:zimbraAdmin"
    )
      
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error creating account %s. Error: %s' % (account, response.get_fault_message()), 
        response = response
      )

    return response.get_response()
       
  def cleanUp(self):
    """ Clean up after one step to leave a dedicated result for the other
     test cases.
    """
    self.setUp()

  def setUp(self):
    """
    Setup everything required to make a request to zimbra server.
    """
    
    self.request = RequestJson()
    self.request = self.comm.gen_request(token=self.token)

  def getDomainId(self, domain):
    """
    Returns the zimbraId of a domain. Useful to modify a domain with ModifyDomainRequest for instance.
    
    domain_id = self.getDomainId(inova.net)
    equal:
    domain_id = '4af850c7-7e44-452e-ad25-c70fda58f9bf'
    """
    
    self.cleanUp() 
    self.request.add_request(
      "GetDomainInfoRequest",
      {
        "domain": {
          "_content": domain,
          "by": "name",
        },
      },
      "urn:zimbraAdmin"
    )
      
    response = self.comm.send_request(self.request)
      
    if response.is_fault():
      raise ZimbraRequestError("Reponse failed: (%s) %s" % (response.get_fault_code(), response.get_fault_message()))
    
    return response.get_response()['GetDomainInfoResponse']['domain']['id']
    
  def getDomainQuotaUsage(self,domain):
    """
     Returns quota usage of all users of a specific domain
      {
      "GetQuotaUsageResponse": {
       "searchTotal": 1294,
       "account": [
        {
        "used": 0,
    "limit": 0,
    "name": "santoro2701.gmail.com@conbras.com",
    "id": "63b128d6-b7f2-466d-ac86-7b253e62a7ed"
     },
     {
    "used": 28,
    "limit": 26843545600,
    "name": "dp.rio@conbras.com",
    "id": "5b4832d1-b642-4778-ab7d-3056ebcefada"
     },
    .
    .
    .
      https://files.zimbra.com/docs/soap_api/8.6.0/api-reference/zimbraAdmin/GetQuotaUsage.html

    """
    self.cleanUp()

    self.request.add_request(
        "GetQuotaUsageRequest",
        {
            "domain": domain,
      "allServers": "1",
      "sortBy": "percentUsed",
      "sortAscending": "1",
        },
        "urn:zimbraAdmin"
    )

    response = self.comm.send_request(self.request)
    
    if response.is_fault():
      raise ZimbraRequestError("Reponse failed: (%s) %s" % (response.get_fault_code(), response.get_fault_message()))
    
    return(response.get_response())

  def getCos(self, cos_name):
    """ Get COS by it's name
    :param cos_name: The name of the COS
    """
    self.cleanUp()
    self.request.add_request(
      request_name = 'GetCosRequest',
      request_dict = {
        'cos' : {
          'by' : 'name',
          '_content' : cos_name
        }
      },
      namespace = 'urn:zimbraAdmin'
    )
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error getting COS %s. Error: %s' % (cos_name, response.get_fault_message()), 
        response = response
      )

    return response.get_response()

  def createCos(self, cos_name, features=dict()):
    """ Create a new cos.
    :param cos_name: The name of the COS
    :param features: A dict representing the feature->value 
    """
    if type(features) is not dict:
      raise TypeError('Wrong type found for features, must be a dict.')

    features_req = []
    for feature, value in features.items():
      features_req.append({
        'n' : feature ,
        '_content' : value
      })

    self.cleanUp()
    self.request.add_request(
      request_name = 'CreateCosRequest',
      request_dict = { 
        'name' : { '_content' : cos_name },
        'a' : features_req
      },
      namespace = 'urn:zimbraAdmin'
    )

    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error creating COS %s Error: %s' % (cos_name, response.get_fault_message()), 
        response = response
      )

    return response.get_response()

  def modifyCos(self, zimbra_cos_id, features):
    """ Update a cos. 
    :param zimbra_cos_id: The zimbraID of the COS
    :param features: A dict representing the feature->value 
    """
    if type(features) is not dict:
      raise TypeError('Wrong type found for features, must be a dict')

    features_req = []
    for feature, value in features.items():
      features_req.append({
        'n' : feature,
        '_content' : value
      })

    self.cleanUp()
    self.request.add_request(
      request_name = 'ModifyCosRequest',
      request_dict = {
        'id' : {
          '_content' : zimbra_cos_id
        },
        'a' : features_req
      },
      namespace = 'urn:zimbraAdmin'
    )

    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error creating COS %s Error: %s' % (cos_name, response.get_fault_message()), 
        response = response
      )
    
    return response.get_response()

  def deleteCos(self, zimbra_cos_id):
    """ Delete a specific COS
    :param zimbra_cos_id: The zimbraID of the COS
    """
    self.cleanUp()
    self.request.add_request(
      request_name = 'DeleteCosRequest',
      request_dict = {
        'id' : { '_content' : zimbra_cos_id }
      },
      namespace = 'urn:zimbraAdmin'
    )
    response = self.comm.send_request(self.request)

    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error creating COS %s Error: %s' % (cos_name, response.get_fault_message()), 
        response = response
      )
      
    return response.get_response()

  def getComputeAggregateQuotaUsage(self):
    """ This method get all quota usage of all domains in a zimbra system. This may take a while depending how many domains and servers you have. Use wisely :P
    """

    self.cleanUp()

    self.request.add_request(
        "ComputeAggregateQuotaUsageRequest",
        {
        },
        "urn:zimbraAdmin"
    )

    response = self.comm.send_request(self.request)

    if response.is_fault():
      raise ZimbraRequestError("Reponse failed: (%s) %s" % (response.get_fault_code(), response.get_fault_message()))

    return(response.get_response())

  def createDistributionList(self, dlist, attrs=list()):
    """ This method create zimbra distribution list. A list of attributes may be given, we will handle it for you.
    :param dlist: The target distribution list
    :param attrs: List of tuple attributes of distribution list
    """
    if not type(attrs) == list:
      raise TypeError('attrs must be a list')

    request_attrs = []
    for attr in attrs:
      zattr, value = attr
      # If it's a list, then it's a multi-value attribute
      if type(value) == list:
        for multi_attr in value:
          request_attrs.append({
            'n' : zattr,
            '_content' : multi_attr
          })
      else:
        request_attrs.append({
          'n' : zattr,
          '_content' : value
        })
    self.cleanUp()
    
    self.request.add_request(
      request_name = "CreateDistributionListRequest",
      request_dict = {
        "name": dlist,
        "a": request_attrs
      },      
      namespace = "urn:zimbraAdmin"
    )
      
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error creating DL %s Error: %s' % (dlist, response.get_fault_message()), 
        response = response
      )

    return response.get_response()

  def getDistributionList(self, dlist):
    """ Gets information about a distribution list.
    :param dlist: The target distribution list
    Obs: Tested with "a" attribute does not have effect on result
    """    
    self.cleanUp()
    self.request.add_request(
      request_name = "GetDistributionListRequest",
      request_dict = {
        "dl": {
          "_content": dlist,
          "by": "name",
        },
      },
      namespace = "urn:zimbraAdmin"
    )
            
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error getting DL: %s Error: %s' % (dlist, response.get_fault_message()), 
        response = response
      )
    
    return response.get_response()

  def deleteDistributionList(self, dlist_zimbra_id):
    """ Deletes distribution list
    :param dlist_zimbra_id: Distribution List zimbraID
    """    
    self.cleanUp() 
    self.request.add_request(
      request_name = "DeleteDistributionListRequest",
      request_dict = { "id" : dlist_zimbra_id },
      namespace = "urn:zimbraAdmin"
    )      
    
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error deleting DL: %s Error: %s' % (dlist, response.get_fault_message()), 
        response = response
      )
    return response.get_response()

  def addDistributionListMember(self, dlist_zimbra_id, members):
    """ This method adds members to a zimbra distribution list. A list of members must be sent.
    This method is idempotent, it will not change the result executing multiple times
    :param dlist_zimbra_id: The target distribution list zimbraId
    :param members: List containing the account members
    """
    if not type(members) == list:
      raise TypeError('members must be a list')

    zmembers = []
    for member in members:
      zmembers.append({'_content': member})
    self.cleanUp()
    
    self.request.add_request(
      request_name = "AddDistributionListMemberRequest",
      request_dict = {
        "id": dlist_zimbra_id,
        "dlm": zmembers
      },      
      namespace = "urn:zimbraAdmin"
    )
      
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error adding members to dlist %s Error: %s' % (dlist_zimbra_id, response.get_fault_message()), 
        response = response
      )

    return response.get_response()

  def grantRight(self, target_name, target_type, grantee_name, grantee_type, right, deny=0):
    """ Grant a right on a target to an individual or group grantee.
    This method is idempotent, it will not change the result executing multiple times
    :param target_name: The target for applying the right (by name). E.g.: 'inova.net'. External docs: /target
    :param target_type: The type of the target. E.g.: 'domain'. External docs: /target@type
    :param grantee_name: Grantee selector. E.g.: 'grp', 'dlist'. External docs: /grantee
    :param grantee_type: The type of the grantee. E.g.: 'grp', 'dlist'. External docs: /grantee@type
    :param right: The name of the right. E.g.: getDomainQuotaUsage, domainAdminConsoleRights. External docs: /right
    :param deny: Either to deny or grant the permission. Default is 0. External docs: /right@deny
    
    Ref. Docs: https://files.zimbra.com/docs/soap_api/8.6.0/api-reference/zimbraAdmin/GrantRight.html    
    """
    self.cleanUp()
    self.request.add_request(
      request_name = "GrantRightRequest",
      request_dict = {
        "target": {
          "type": target_type,
          "by": "name",
          "_content": target_name
        },
        "grantee": {
          "type": grantee_type,
        "by": "name",
          "_content": grantee_name
        },  
        "right": {
        "_content": right,
        "deny": deny
        }
      },
      namespace = "urn:zimbraAdmin"
    )
    response = self.comm.send_request(self.request)
    if response.is_fault():
      raise ZimbraRequestError(
        message = 'Error adding grant to target_name %s Error: %s' % (target_name, response.get_fault_message()), 
        response = response
      )

    return response.get_response()
