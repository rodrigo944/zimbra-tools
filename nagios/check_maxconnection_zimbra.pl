#!/usr/bin/perl
use strict;
use warnings;
use Getopt::Long;
use DBI;

my $help;
my $critical;
my $warning;
my $host;
my $user;
my $passwd;
my $port;

GetOptions(
           'critical=i' => \$critical,
           'warning=i'  => \$warning,
           'host=s'     => \$host,
           'user=s'     => \$user,
           'passwd=s'   => \$passwd,
           'port=s'     => \$port,
           );

if( !$critical || !$warning || !$host || !$user ) {
        usage();
        exit 2;
}

my $dsn = ("DBI:mysql:zimbra:$host:7306");

my $dbh = DBI->connect($dsn, $user, $passwd);

my $sleep = 0;
my $locked = 0;
my $active = 0;

my $sql = 'SHOW VARIABLES LIKE ' . $dbh->quote('max_connections');

my $sth = $dbh->prepare($sql);
$sth->execute();

my $ref = $sth->fetchrow_hashref();

my $max_connections = $ref->{Value};

my $sqlShow = 'SHOW PROCESSLIST';

my $sthShow = $dbh->prepare($sqlShow);
$sthShow->execute();

my $actual_connections = $sthShow->rows();

while ( my $ref = $sthShow->fetchrow_hashref() ) {
        if ( $ref->{Command} eq 'Sleep' ) {
                $sleep++;
        } elsif ( $ref->{Command} eq 'Locked' ) {
                $locked++;
        } else {
                $active++;
        }
}

my $pct = $actual_connections / $max_connections * 100.0;

if ( ( $pct < $warning ) && ( $pct < $critical ) ) {
        print "Total Connections: $actual_connections Active: $active Locked: $locked Sleep: $sleep";
        exit 0;
}

if ( ( $pct > $warning ) && ( $pct < $critical ) )  {
        print "Total Connections: $actual_connections Active: $active Locked: $locked Sleep: $sleep";
        exit 1;
}
else {
        print "Total Connections: $actual_connections Active: $active Locked: $locked Sleep: $sleep";
        exit 2;
}

sub usage {
        print "$0 --host=<host> --user=<user> --passwd=<passwd> --warning=<warning treshold> --critical=<critical treshold>\n";
        exit 2;
}

$sthShow->finish();
$dbh->disconnect;
