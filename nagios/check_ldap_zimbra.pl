#!/usr/bin/perl
use warnings;
use strict;
use Net::LDAP;

my $server = shift;
my $root = shift;
my $secrets = shift;

my $servername = $server;
my $rootDn     = 'cn='.$root;
my $secret     = $secrets;

my $ldap = Net::LDAP->new( $servername ) or exit 2;

if ( defined($ldap) ) {
        $ldap->bind( $rootDn, password=> $secret, version => 3 ) or exit 2;
        my $msg = $ldap->search(
                        base => $rootDn,
                        scope => 'one',
                        filter => '(objectClass=*)'
                );
                if ( $msg->is_error() ) {
                        print "ERROR: Problems with ldap search";
                        exit 2;
                }
                else {
                        print "OK: LDAP is up and running!";
                        exit 0;
                }
}
else {
        print "ERROR: problems connecting with server";
        exit 2;
}
