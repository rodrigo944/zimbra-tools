#!/usr/bin/perl
#
# Script de check imap logando e verificando as caixas do usuario
#
use strict;
use warnings;
use Net::IMAP::Simple;
use Getopt::Long;

my $server;
my $user;
my $passwd;

GetOptions(
  "server=s" => \$server,
  "user=s"   => \$user,
  "passwd=s" => \$passwd,
);

if ( !$server || !$user || !$passwd ) {
  print "$0 --server=<server> --user=<user> --passwd=<passwd>\n";
  exit 3;
}

my $imap = Net::IMAP::Simple->new($server);

if ( !$imap ) {
  print "Server is down: ".$imap->errstr."\n";
  exit 2;
}

my $return = $imap->login($user, $passwd);
if(!$return) {
  print "Auth error! ".$imap->errstr."\n";
  exit 2;
}

my @mailboxes = $imap->mailboxes();

if ( @mailboxes > 0 ) {
  print "Logged in!\n";
  print "Mailboxes: ".join(", ", @mailboxes)."\n";
  exit 0;
}
else {
  print "Logged in but cant find the mailboxes\n";
  exit 1;
}

$imap->quit();