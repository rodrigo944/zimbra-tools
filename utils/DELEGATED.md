### Pre Requirements

argparse
python-zimbra

### Installer

Tested on ubuntu 14

```bash
curl --silent -L https://raw.githubusercontent.com/inova-tecnologias/zimbra-tools/master/utils/zdelegated_bootstrap.sh | sudo sh -s --
```

zdelegated --help

#### Creating a new delegated user with default grants

```bash
zdelegated -a target_delegated_account@mydomain.tld --admin global_admin@mydomain.tld --dlist mydomain_tld_perms@inova.net -s zimbra_server_hostname
```

#### Appeding an user to a perm delegated distribution list

```bash
# The user target_delegated_account@mydomain.tld will not be created
zdelegated -a target_delegated_account@mydomain.tld --admin global_admin@mydomain.tld --dlist mydomain_tld_perms@inova.net -s zimbra_server_hostname --append
```

#### Adding additional grants

```bash
zdelegated -a target_delegated_account@mydomain.tld --admin global_admin@mydomain.tld --dlist mydomain_tld_perms@inova.net -s zimbra_server_hostname --grants Grant01,Grant02
```


#### Debbuging

```bash
zdelegated -a target_delegated_account@mydomain.tld --admin global_admin@mydomain.tld --dlist mydomain_tld_perms@inova.net -s zimbra_server_hostname --debug
```
