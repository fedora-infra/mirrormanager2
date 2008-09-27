#!/usr/bin/perl -w
# ftp://ftp.ripe.net/ripe/dbase/split/ripe.db.aut-num.gz

use strict;

my (%obj, %x);

my $state = 0;
my $lastobj;
my $lastattr;
while (<>) {
	s/[\n\r\s]+$//;
	next if /^%/;
	s/#.*$//; #?

#	print "[$state] $_\n";
	if ($state == 0) {			# wait for a new record
		if		(/^$/) {
		} elsif (/^aut-num:\s+(\S+)/) {
			$lastobj = $1;
			$obj{$lastobj} = { };
			$state = 1;
		} elsif (/^(\S+):/) {
			print "DISCARDED: $1\n";
			$state = 99;
		}
	} elsif ($state == 1) {
		if (/^$/) {
			$state = 0;
		} elsif (/^([a-z-]+):(?:\s+(.+))?/) {
			my $value = $2 || '';
			$lastattr = $1;
#			print "<$lastobj><$lastattr>\n";
#			use Data::Dumper; print Data::Dumper->Dumpxs([\%obj], ['*obj']);
#			BEWARE! This merges multiple attributes!
			if (exists $obj{$lastobj}->{$lastattr}) {
				$obj{$lastobj}->{$lastattr} .= "\n" . $value;
			} else {
				$obj{$lastobj}->{$lastattr} .= $value;
			}
		# XXX what does the + really mean?
		} elsif (/^(?:\+?\s+|\+)(.*)/) {	# continued attribute
			$obj{$lastobj}->{$lastattr} .= "\n" . ($1 || '');
		} else {
			print STDERR "[$state][$lastobj] $_\n";
			die;
		}
	} elsif ($state == 99) {	# eat the current record
		if (/^$/) {
			$state = 0;
		}
	} else { die "UNKNOWN STATE: $state" }
}

foreach (keys %obj) {
	my $d = $obj{$_}->{descr};
	$d =~ s/\n.*$//mg;
	print "$_ $obj{$_}->{'as-name'} $d\n";
}

