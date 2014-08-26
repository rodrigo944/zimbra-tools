""" Requires: perl-LDAP
Script for migrating new accounts from other zimbra system
"""
#!/usr/bin/perl
use warnings;
use strict;
use Net::LDAP;
use XML::Simple;
use Getopt::Long;
use Data::Dumper;

# CONF.
my @getAttributes = (
        'displayName',
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
        'userPassword',
        ); 

#my $migrationCOSId = '2a2be249-c436-44d0-b164-9c3c2b23f239';
my $migrationCOSId = 'dde3caa3-f539-4ef1-a02b-f5983f488985';
my $defaultDatePop3DownloadSince = '20140328170000Z';

my $localconfig = 'localconfig.xml';
my $dListProv = '/tmp/dListProv.zm';

my $xml = new XML::Simple;
my $localconfig_xml = $xml->XMLin($localconfig);
my %ldap_conf = (
        host => $localconfig_xml->{key}->{ldap_host}->{value},
        binddn => $localconfig_xml->{key}->{zimbra_ldap_userdn}->{value},
        password => $localconfig_xml->{key}->{zimbra_ldap_password}->{value},
        );



my $ldap_query = '(&(objectClass=zimbraAccount)(!(objectClass=zimbraCalendarResource))(!(zimbraIsSystemResource=TRUE)))';
&provAccount($ldap_query);

$ldap_query = '(&(objectClass=zimbraDistributionList))';
&provDL($ldap_query);

sub provAccount{
    my $ldap_filter = shift; my @ldap_attrs = shift;

    my $ldap = Net::LDAP->new($ldap_conf{host}) || die "$@";
    $ldap->bind($ldap_conf{binddn} , password => $ldap_conf{password});


    my $ldap_search = $ldap->search (
            scope => 'sub',
            filter => $ldap_filter,
            attrs => @ldap_attrs,
            );


# if error
    $ldap_search->code && die $ldap_search->error;

    my %zmprov;
    foreach my $entry ( $ldap_search->entries)
    {

        my $email = $entry->get_value('zimbraMailDeliveryAddress');

          
        print "createAccount $email tempINOVA2013 zimbraCOSId $migrationCOSId";   
        for my $attr (@getAttributes)
        {

            if ( $entry->get_value($attr) )
            {   
                print " $attr ";
                foreach ( $entry->get_value($attr) )
                {
                    my $value = $_;
                    $value =~ s|\n|\\n|g;
                    $value =~ s|'|\\'|g;

                    print "'$value' ";
                }
            }

        }

        print "\n";
    
        for my $mailAlias ( $entry->get_value('zimbraMailAlias') )
        {
            print "addAccountAlias $email $mailAlias\n";
        } 
    }


}

sub provDL{
    my $ldap_filter = shift; my @ldap_attrs = shift;

    my $ldap = Net::LDAP->new($ldap_conf{host}) || die "$@";
    $ldap->bind($ldap_conf{binddn} , password => $ldap_conf{password});


    my $ldap_search = $ldap->search (
            scope => 'sub',
            filter => $ldap_filter,
            attrs => @ldap_attrs,
            );


# if error
    $ldap_search->code && die $ldap_search->error;

    foreach my $entry ( $ldap_search->entries)
    {

        my $dl = $entry->get_value('mail');
        print "createDistributionList $dl\n";
        print "addDistributionListMember $dl";

        for my $member ( $entry->get_value('zimbraMailForwardingAddress') )
        {
            print " $member ";
        }       
        print "\n";
    }

    print "\n";


}

