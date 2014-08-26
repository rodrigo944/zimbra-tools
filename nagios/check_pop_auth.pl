#!/usr/bin/perl

use strict;
use IO::Socket qw(SOCK_STREAM);

my $s = IO::Socket::INET->new( PeerAddr  => $ARGV[0],
                                  PeerPort  => 110,
                                  Proto     => "tcp",
                                  Type      => SOCK_STREAM,
                                  LocalAddr => undef,
                                  Timeout   => 30 )
        or
          print "could not connect socket $ARGV[0]: $!" 
            and print "$ARGV[0]" and exit 2;

$s->autoflush( 1 );

defined(my $msg = &sockread()) or print "Could not read" and return 0;
chomp $msg;
#print $msg."\n";

print $s "user $ARGV[1]\015\012";
defined(my $msg = &sockread()) or print "Could not read" and return 0;
chomp $msg;
#print $msg."\n";

print $s "pass $ARGV[2]\015\012";
defined(my $msg = &sockread()) or print "Could not read" and return 0;
chomp $msg;
#print $msg."\n";

if ($msg =~ /\+OK/) {
        print "Okay\n";
        $s->close;
        exit 0;
} else {
        print "Problemas em $ARGV[0]\n";
        $s->close;
        exit 2;
}

sub sockread {
  my $line = $s->getline();
  unless (defined $line) {
      return;
  }

  # Macs seem to leave CR's or LF's sitting on the socket.  This
  # removes them.
  $line =~ s/^[\r]+//;

  $line =~ /^[\\+\\-](OK|ERR)/i && do {
    my $l = $line;
    chomp $l;
  };
  return $line;
}
