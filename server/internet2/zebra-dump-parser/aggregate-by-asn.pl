#!/usr/bin/perl -w

use strict;
use Net::IP; # libnet-ip-perl

my %as;
while (<>) {
	my ($pref, $asn) = split;
	push(@{$as{$asn}}, $pref);
}

foreach my $asn (keys %as) {
	if (scalar @{$as{$asn}} <= 1) {
		print @{$as{$asn}}[0] . " $asn\n";
		next;
	}

	my @nets = map { Net::IP->new($_) or die "Not an IP: $_" } @{$as{$asn}};
	sort_networks(\@nets);
	#remove_overlaps(\@nets);
	aggregate(\@nets);
	print $_->prefix . " $asn\n" foreach @nets;
}
exit 0;

sub sort_networks {
	my $addrs = $_[0];

	@$addrs = sort {
		$a->bincomp('lt', $b) ? -1 : ($a->bincomp('gt', $b) ? 1 : 0);
	} @$addrs;
}

# this function is unfinished...
sub aggregate {
	my $addrs = $_[0];

	# continue aggregating until there are no more changes to do
	my $changed = 1;
	while ($changed) {
		$changed = 0;
		my @new_addrs;
		my $prev = $addrs->[0];
		foreach my $cur (@$addrs[1 .. $#{$addrs}]) {
			if (my $aggregated = $prev->aggregate($cur)) {
					$prev = $aggregated;
					$changed = 1;
			} else {
					push(@new_addrs, $prev);
					$prev = $cur;
			}
		}
		push(@new_addrs, $prev);
		@$addrs = @new_addrs;
	}
}

sub remove_overlaps {
	my $addrs = $_[0];

	my @nets;
	my $prev = $addrs->[0];
	foreach my $cur (@$addrs[1..$#{$addrs}]) {
		my $how = $prev->overlaps($cur);
		if      ($how == $IP_NO_OVERLAP) {
			push(@nets, $prev);
		} elsif ($how == $IP_A_IN_B_OVERLAP) { # cur contains prev
			warn "A IN B  p:".$prev->prefix." c:".$cur->prefix."\n";
			push(@nets, $prev);
		} elsif ($how == $IP_B_IN_A_OVERLAP) { # prev contains cur
			warn "B IN A  p:".$prev->prefix." c:".$cur->prefix."\n";
			push(@nets, $prev);
		} elsif ($how == $IP_IDENTICAL) {
#		} elsif ($how == $IP_PARTIAL_OVERLAP) {
		} else {
			warn "Error: " . $prev->prefix . " overlaps " . $cur->prefix
				. " ($how).\n";
#			push(@nets, $prev); # ???
		}
		$prev = $cur;
	}
	@$addrs = @nets;
}

