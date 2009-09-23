#!/usr/bin/perl -w

use strict;
use Getopt::Long;
use Net::Patricia;

my ($BGP_Dump, $AS_Names, $input);
GetOptions(
	'routes=s'		=> \$BGP_Dump,	# route2country_NO_DATE
	'as-names=s'	=> \$AS_Names,	# asn-ctl.txt
	'input=s'		=> \$input,
) or exit 1;

die "missing parameter" if not $BGP_Dump or not $AS_Names;

my $pt = new Net::Patricia;

open(BGPDUMP, $BGP_Dump) or die "cannot open $BGP_Dump: $!";
while (<BGPDUMP>) {
#	eval { $pt->add_string((split())[0, 3]) };
	eval { $pt->add_string(split) };
	warn "add_string($_): $@" if $@;
}
close BGPDUMP;

my %as_name;
open(ASNAMES, $AS_Names) or die "cannot open $AS_Names: $!";
while (<ASNAMES>) {
	s/^AS//;
	s/\n//;
	s/#.*$//;
#	my ($as, $desc) = split(/\s+/, $_, 2);
	my ($as, undef, undef, $desc) = split(/\s+/, $_, 4);
	$as_name{$as} = $desc;
}
close ASNAMES;

if ($input) {
	open(INPUT, $input) or die "cannot open $input: $!\n";
} else {
	open(INPUT, '<&STDIN') or die;
}

my %by_asn;
my $total = 0;
while (<INPUT>) {
	my ($queries, $ip) = split;

	next if not $ip;
	my $asn = eval { $pt->match_string($ip) };
	warn "match_string($ip): $@" if $@;
	$asn ||= " UNKN  ($ip)";
	if (exists $by_asn{$asn}) {
		$by_asn{$asn} += $queries;
	} else {
		$by_asn{$asn} = $queries;
	}
	$total += $queries;
}
close INPUT if $input;

print "Total queries: $total\n\n";
print "     queries  ASN\n------+--------+-----\n";
foreach (reverse sort { $by_asn{$a} <=> $by_asn{$b} } keys %by_asn) {
	my $perc = ($by_asn{$_} * 100) / $total;
	printf('%02.2f%% %8d %5s', $perc, $by_asn{$_}, $_);
	print "  $as_name{$_}" if exists $as_name{$_};
	print "\n";
}

exit 0;

