#!/usr/bin/perl -w
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This work is inspired by the route_btoa.pl program by Craig Labovitz
# <labovit@merit.edu>, which is part of the MRT distribution.
#
# Documentation about the zebra/MRT packet format:
# http://www.mrtd.net/mrt_doc/html/mrtprogrammer.html
# http://manticore.2y.net/doc/zebra/PBDF.html
# http://www.sprintlabs.com/Department/IP-Interworking/Routing/PyRT/README.mrtd
# http://www.ripe.net/projects/ris/docs/asn.html
# http://tools.ietf.org/id/draft-ietf-grow-mrt-04.txt

use strict;
require 5.008;

# only meaningful for message types TABLE_DUMP and TABLE_DUMP_V2
# 1: verbose dump  2: AS path  3: origin AS
my $format = 3;
my $ignore_v6_routes = 0;

##############################################################################
use constant {
	MSG_BGP						=> 5,	# MRT only
	MSG_BGP4PLUS				=> 9,	# MRT only
	MSG_TABLE_DUMP				=> 12,	# dump bgp routes-mrt
	MSG_TABLE_DUMP_V2			=> 13,	# RIPE RIS
	MSG_BGP4MP					=> 16,	# dump bgp all

	BGP4MP_STATE_CHANGE			=> 0,
	BGP4MP_MESSAGE				=> 1,
	BGP4MP_ENTRY				=> 2,
	BGP4MP_SNAPSHOT				=> 3,

	AFI_IP						=> 1,
	AFI_IP6						=> 2,

	# for TABLE_DUMP_V2
	INDEX_TABLE					=> 1,
	RIB_IPV4_UNICAST			=> 2,
	RIB_IPV4_MULTICAST			=> 3,
	RIB_IPV6_UNICAST			=> 4,
	RIB_IPV6_MULTICAST			=> 5,
	RIB_GENERIC					=> 6,

	BGP_TYPE_OPEN				=> 1,
	BGP_TYPE_UPDATE				=> 2,
	BGP_TYPE_NOTIFICATION		=> 3,
	BGP_TYPE_KEEPALIVE			=> 4,

	BGP_ATTR_FLAG_EXTLEN		=> 0x10,

	AS_SET						=> 1,

	BGP_ATTR_ORIGIN				=> 1,
	BGP_ATTR_AS_PATH			=> 2,
	BGP_ATTR_NEXT_HOP			=> 3,
	BGP_ATTR_MULTI_EXIT_DISC	=> 4,
	BGP_ATTR_LOCAL_PREF			=> 5,
	BGP_ATTR_ATOMIC_AGGREGATE	=> 6,
	BGP_ATTR_AGGREGATOR			=> 7,
	BGP_ATTR_COMMUNITIES		=> 8,
#	BGP_ATTR_ORIGINATOR_ID		=> 9,
#	BGP_ATTR_CLUSTER_LIST		=> 10,
##	BGP_ATTR_DPA				=> 11,
#	BGP_ATTR_ADVERTISER			=> 12,
##	BGP_ATTR_RCID_PATH			=> 13,
	BGP_ATTR_MP_REACH_NLRI		=> 14,
	BGP_ATTR_MP_UNREACH_NLRI	=> 15,
	BGP_ATTR_EXT_COMMUNITIES	=> 16,
	BGP_ATTR_LARGE_COMMUNITIES	=> 32,
};

my @BGP_ORIGIN = qw(IGP EGP Incomplete);

##############################################################################
open(INPUT, '-') or die "Could not open INPUT $!\n";

use constant BUF_READ_SIZE => 4096 * 8;
my $buf = '';
my $read_done = 0;

my @BGP_Peers; # used by the TABLE_DUMP_V2 parser

while (1) {
	if ($read_done) {
		last if length $buf == 0;
	} elsif (length $buf < BUF_READ_SIZE) {
		my $tmp = '';
		my $n = sysread(INPUT, $tmp, BUF_READ_SIZE * 2);
		die "sysread: $!" if not defined $n;
		$read_done = 1 if $n == 0;
		$buf .= $tmp;
	}

	die "short file (empty packet)" if not $buf;
	my $header = substr($buf, 0, 12, '');
	my ($time, $type, $subtype, $packet_length) = unpack('N n n N', $header);
	my $packet = substr($buf, 0, $packet_length, '');
	die "short file (got " . (length $packet) . " of $packet_length bytes)"
		if $packet_length != length $packet;

	if ($format == 1) {
		my ($sec, $min, $hour, $mday, $mon, $year, @junk) = localtime($time);
		$mon++;
		$year += 1900;
		printf("\nTIME: $year-$mon-$mday %02d:%02d:%02d\n", $hour, $min, $sec);
	}

	decode_mrt_packet(\$packet, $type, $subtype);
}
exit 0;

##############################################################################
sub decode_mrt_packet {
	my ($pkt, $type, $subtype) = @_;

	if ($type == MSG_TABLE_DUMP) { ###########################################
		my $af = $subtype;
		my $header_format;

		if ($af == AFI_IP) {
			$header_format = 'n n a4 C C N a4 n n/a';
		} elsif ($af == AFI_IP6) {
			return if $ignore_v6_routes;
			$header_format = 'n n a16 C C N a16 n n/a';
		} else {
			warn "TYPE: MSG_TABLE_DUMP/AFI_UNKNOWN_$af\n";
			return;
		}

		my ($viewno, $seq_num, $prefix, $prefixlen, undef, $originated,
			$peerip, $peer_as, $attributes) = unpack($header_format, $$pkt);
		my $attr = parse_attributes($attributes);

		if ($format == 1) {
			print "TYPE: MSG_TABLE_DUMP/" .
					($af == AFI_IP ? 'AFI_IP' : 'AFI_IP6') . "\n"
				. "VIEW: $viewno  SEQUENCE: $seq_num\n"
				. 'PREFIX: ' . inet_ntop($af, $prefix) . "/$prefixlen\n"
				. "ORIGINATED: " . localtime($originated) . "\n";
			print 'FROM: ' . inet_ntop($af, $peerip) . " AS$peer_as\n"
				if $peer_as;
			print_verbose_attributes($attr);
		} elsif ($format == 2) {
			print inet_ntop($af, $prefix) . "/$prefixlen"
				. print_aspath($attr->[BGP_ATTR_AS_PATH]) . "\n";
		} elsif ($format == 3) {
			print inet_ntop($af, $prefix) . "/$prefixlen "
					. unpack('n', origin_as($attr->[BGP_ATTR_AS_PATH])) . "\n"
				if @{$attr->[BGP_ATTR_AS_PATH]};
		} else { die }
	} elsif ($type == MSG_TABLE_DUMP_V2) { ###################################
		my $af;

		if ($subtype == INDEX_TABLE) {
			my ($collector_id, $view_name, $peers_count, $rest)
				= unpack('a4 n/a n a*', $$pkt);
			$view_name ||= '';
			print "TYPE: MSG_TABLE_DUMP_V2/INDEX_TABLE\n".
				"ID: " . inet_ntoa($collector_id) .
				"\nVIEW_NAME: \"$view_name\", PEERS: $peers_count\n"
					if $format == 1;

			# unpack each peer
			my $peer_index = 0;
			while (length $rest > 0) {
				# parse only the first byte (peer type, a bit field) to
				# known the length of the other fields of $rest
				my ($addrv6, $as32) = split(//, unpack('b8', $rest));
				my $as_size = $as32 ? 4 : 2;
				my $mformat = 'x N' . ($addrv6 ? 'a16' : 'a4') . "a$as_size a*";

				my ($bgp_id, $peer_ip, $peer_as);
				($bgp_id, $peer_ip, $peer_as, $rest) = unpack($mformat, $rest);
				$peer_as = pretty_as($peer_as);

				my $afi = $addrv6 ? AFI_IP6 : AFI_IP;
				print "      PEER $peer_index: ID: $bgp_id, " 
					. inet_ntop($afi, $peer_ip) . ", AS$peer_as\n"
						if $format == 1;
				$BGP_Peers[$peer_index++] = [
					$bgp_id, $afi, $peer_ip, $peer_as, $as_size,
				];
			}

			return;
		} elsif ($subtype == RIB_IPV4_UNICAST) {
			$af = AFI_IP;
		} elsif ($subtype == RIB_IPV4_MULTICAST) {
			return if $ignore_v6_routes;
			$af = AFI_IP;
		} elsif ($subtype == RIB_IPV6_UNICAST) {
			return if $ignore_v6_routes;
			$af = AFI_IP6;
		} elsif ($subtype == RIB_IPV6_MULTICAST) {
			return if $ignore_v6_routes;
			$af = AFI_IP6;
		} elsif ($subtype == RIB_GENERIC) {
			my ($seq_num, $afi, $safi, $nlri) = unpack('N n C a*', $$pkt);
			#my (?, $entry_count, $rest) = unpack("? n a*", $nlri);
			print "TYPE: MSG_TABLE_DUMP_V2/RIB_GENERIC\n"
				. "SEQUENCE: $seq_num\n"
				. "AFI: $afi, SAFI: $safi, NLRI(" . length($nlri) ."):\n";
			hexdump($nlri);
			return;
		} else {
			warn "TYPE: MSG_TABLE_DUMP_V2/UNKNOWN_SUBTYPE_$subtype\n";
			return;
		}

		my ($seq_num, $prefixlen, $nlri) = unpack('N C a*', $$pkt);
		my $bytes = int($prefixlen / 8) + ($prefixlen % 8 ? 1 : 0);
		my ($prefix, $entry_count, $rest) = unpack("a$bytes n a*", $nlri);
		$prefix .= "\0" x (($af == AFI_IP ? 4 : 16) - $bytes); # pad with NULs

		while (length $rest > 0) {
			my ($peer_index, $originated, $attributes);
			($peer_index, $originated, $attributes, $rest)
				= unpack('n N n/a a*', $rest);
			my $attr = parse_attributes($attributes,
				$BGP_Peers[$peer_index]->[4]);

			if ($format == 1) {
				print "TYPE: MSG_TABLE_DUMP_V2/ENTRY_" .
						($af == AFI_IP ? 'AFI_IP' : 'AFI_IP6') . "\n"
					. "SEQUENCE: $seq_num\n"
					. 'PREFIX: ' . inet_ntop($af, $prefix) . "/$prefixlen\n"
					. "ORIGINATED: " . localtime($originated) . "\n";
				my $peer_as = $BGP_Peers[$peer_index]->[3];
				print 'FROM: ' . inet_ntop($af, $BGP_Peers[$peer_index]->[2])
					. " AS$peer_as\n";
				print_verbose_attributes($attr);
				print "-\n";
			} elsif ($format == 2) {
				print inet_ntop($af, $prefix) . "/$prefixlen"
					. print_aspath($attr->[BGP_ATTR_AS_PATH]) . "\n";
			} elsif ($format == 3) {
				print inet_ntop($af, $prefix) . "/$prefixlen "
						. unpack($BGP_Peers[$peer_index]->[4] == 2 ? 'n' : 'N',
							origin_as($attr->[BGP_ATTR_AS_PATH])) . "\n"
					if @{$attr->[BGP_ATTR_AS_PATH]};
			} else { die }
		}

	} elsif ($type == MSG_BGP4MP) { ##########################################
		if ($subtype == BGP4MP_STATE_CHANGE) { #------------------------------
			my ($srcas, $dstas, $ifidx, $af, $rest) = unpack('nnnn a*', $$pkt);
			my $unpack_format;

			if ($af == AFI_IP) {
				$unpack_format = 'a4 a4 n n';
			} elsif ($af == AFI_IP6) {
				$unpack_format = 'C16 C16 n n';
			} else {
				warn "TYPE: BGP4MP/BGP4MP_STATE_CHANGE AFI_UNKNOWN_$af\n";
				return;
			}

			my ($srcip, $dstip, $old_state, $new_state)
				= unpack($unpack_format, $rest);
			print "TYPE: BGP4MP/BGP4MP_STATE_CHANGE " .
					($af == AFI_IP ? 'AFI_IP' : 'AFI_IP6' ) . "\n";
			print "FROM: " . inet_ntop($af, $srcip) . "\n" if notnull($srcip);
			print "TO: "   . inet_ntop($af, $dstip) . "\n" if notnull($dstip);
			print "OLD STATE: $old_state  NEW STATE: $new_state\n";
			# state numbers: see RFC 4271, Appendix 1
			# 1:IDLE 2:CONNECT 3:ACTIVE 4:OPENSENT 5:OPENCONFIRM 6:ESTABLISHED
		} elsif ($subtype == BGP4MP_MESSAGE) { #------------------------------
			my ($srcas, $dstas, $ifidx, $af, $rest) = unpack('nnnn a*', $$pkt);

			my $unpack_format;
			if ($af == AFI_IP) {
				$unpack_format = 'a4 a4 a*';
			} elsif ($af == AFI_IP6) {
				$unpack_format = 'C16 C16 a*';
			} else {
				warn "TYPE: BGP4MP/BGP4MP_MESSAGE AFI_UNKNOWN_$af\n";
				return;
			}

			my ($srcip, $dstip, $bgppkt) = unpack($unpack_format, $rest);
			print "TYPE: BGP4MP/BGP4MP_MESSAGE " .
					($af == AFI_IP ? 'AFI_IP' : 'AFI_IP6' ) . "\n";
			print "FROM: " . inet_ntop($af, $srcip) . "\n" if notnull($srcip);
			print "TO: "   . inet_ntop($af, $dstip) . "\n" if notnull($dstip);
			parse_bgp_packet($bgppkt);
		} elsif ($subtype == BGP4MP_ENTRY) { #--------------------------------
			warn "NOT TESTED"; # XXX
			my ($view, $status, $time_change, $afi, $safi, $next_hop, $prefix,
				$attributes) = unpack('n n N n C C/a C/a n/a', $$pkt);
			my $attr = parse_attributes($attributes);

			print "TYPE: BGP4MP/BGP4MP_ENTRY "
				. ($afi == AFI_IP ? 'AFI_IP' : 'AFI_IP6' ) . "\n";
			print_verbose_attributes($attr);
		} else { #------------------------------------------------------------
			print "TYPE: BGP4MP/BGP4MP_UNKNOWN-$subtype\n";
			hexdump($$pkt);
		}
	} elsif ($type == MSG_BGP4PLUS ###########################################
		  or $type == MSG_BGP) { #############################################
		my $unpack_format = ($type == MSG_BGP4PLUS)
			? 'n C16 n C16 n/a n/a a*' : 'n a4 n a4 n/a n/a a*';
		my $afi = ($type == MSG_BGP4PLUS) ? AFI_IP6 : AFI_IP;
		my ($srcas, $srcip, $dstas, $dstip, $unf_routes, $attributes, $nlri)
			= unpack($unpack_format, $$pkt);
		my $attr = parse_attributes($attributes);

		print "TYPE: TYPE: BGP4MP/BGP4"
			. ($afi == AFI_IP ? '' : 'PLUS') . "/UPDATE\n";
		print "FROM: " . inet_ntop($afi, $srcip) . " AS$srcas\n" if $srcas;
		print "TO: "   . inet_ntop($afi, $dstip) . " AS$dstas\n" if $dstas;
		print_verbose_attributes($attr);
		print "WITHDRAWN: $_\n" foreach (parse_nlri_prefixes($unf_routes));
		print "ANNOUNCE: $_\n" foreach (parse_nlri_prefixes($nlri));
	} else { ################################################################
		warn "UNKNOWN TYPE: $type  SUBTYPE: $subtype\n";
	}
}

sub parse_attributes {
	my ($attributes, $as_size) = @_;
	my @attr;

	while (length $attributes > 0) {
		my ($flags, $type);
		($flags, $type, $attributes) = unpack('C C a*', $attributes);

		my $attrib; # content of the next attribute
		if ($flags & BGP_ATTR_FLAG_EXTLEN) {
			($attrib, $attributes) = unpack('n/a a*', $attributes);
		} else {
			($attrib, $attributes) = unpack('C/a a*', $attributes);
		}

		if ($type == BGP_ATTR_ORIGIN) {
			$attr[BGP_ATTR_ORIGIN] = unpack('C', $attrib);
		} elsif ($type == BGP_ATTR_AS_PATH) {
			$attr[BGP_ATTR_AS_PATH] = [ ];
			$as_size ||= 2;
			while (length $attrib > 0) {
				my ($seg_type, $seg_length);
				($seg_type, $seg_length, $attrib) = unpack('C C a*', $attrib);
				my $seg_value = substr($attrib, 0, $seg_length * $as_size, '');
				push(@{$attr[BGP_ATTR_AS_PATH]},
					[ $seg_type, [ unpack("(a$as_size)*", $seg_value) ] ]);
			}
		} elsif ($type == BGP_ATTR_NEXT_HOP) {
			$attr[BGP_ATTR_NEXT_HOP] = $attrib;				# IPv4
		} elsif ($type == BGP_ATTR_MULTI_EXIT_DISC) {
			$attr[BGP_ATTR_MULTI_EXIT_DISC] = $attrib;		# 'N'
		} elsif ($type == BGP_ATTR_LOCAL_PREF) {
			$attr[BGP_ATTR_LOCAL_PREF] = $attrib;			# 'N'
		} elsif ($type == BGP_ATTR_ATOMIC_AGGREGATE) {
			$attr[BGP_ATTR_ATOMIC_AGGREGATE] = 1;
		} elsif ($type == BGP_ATTR_AGGREGATOR) {
			$attr[BGP_ATTR_AGGREGATOR] = [ unpack('a2 a4', $attrib) ];# N, IPv4
		} elsif ($type == BGP_ATTR_COMMUNITIES) {
			$attr[BGP_ATTR_COMMUNITIES] = [ ];
			while (length $attrib > 0) {
				my $community = substr($attrib, 0, 4, '');
				push(@{$attr[BGP_ATTR_COMMUNITIES]}, $community);
			}
		} elsif ($type == BGP_ATTR_LARGE_COMMUNITIES) {
			$attr[BGP_ATTR_LARGE_COMMUNITIES] = [ ];
			while (length $attrib > 0) {
				my $community = substr($attrib, 0, 12, '');
				push(@{$attr[BGP_ATTR_LARGE_COMMUNITIES]}, $community);
			}
		} elsif ($type == BGP_ATTR_MP_REACH_NLRI) {
			# FIXME v2 uses a different format
			my ($afi, $safi, $next_hop, $rest) = unpack('n C C/a a*', $attrib);

			# XXX how should I deal with all these cases?
			my $next_hop_len = length $next_hop;
			my ($next_hop_global_in, $next_hop_global, $next_hop_local);
			if		($next_hop_len == 4) {
				$next_hop_global_in = $next_hop;
			} elsif ($next_hop_len == 12) {
				my ($rd_high, $rd_low);
				($rd_high, $rd_low, $next_hop_global_in)
					= unpack('N N a4', $next_hop);
			} elsif ($next_hop_len == 16) {
				$next_hop_global = $next_hop;
			} elsif ($next_hop_len == 32) {
				($next_hop_global, $next_hop_local)
					= unpack('a16 a16', $next_hop);
			} else { die }

			my $num_snpa;
			($num_snpa, $rest) = unpack('C a*', $rest);
			while ($num_snpa-- > 0) {
				my $snpa;
				($snpa, $rest) = unpack('C/a a*', $rest);
				print "|SNPA: "; hexdump($snpa); # XXX
			}

			if ($format == 1) { # XXX should not print here...
			print "|AFI: $afi ($safi)\n";
			print "|NEXT_HOP: " . inet6_ntoa($next_hop_global)
				. "  (LENGTH: $next_hop_len)\n";
			print "|ANNOUNCE: $_\n" foreach (parse_nlri_prefixes($rest, $afi));
			}
		} elsif ($type == BGP_ATTR_MP_UNREACH_NLRI) {
			my ($afi, $safi, $nlri) = unpack('n C a*', $attrib);

			if ($format == 1) { # XXX
			print "|WITHDRAWN: $_\n" foreach(parse_nlri_prefixes($nlri, $afi));
			}
		} else {
			warn "Unknown BGP attribute $type (flags: $flags)\n";
		}
	}

	return \@attr;
}

sub parse_bgp_packet {
	my ($bgppkt) = @_;

	my ($marker, $length, $type, $data) = unpack('a16 n C a*', $bgppkt);

	if		($type == BGP_TYPE_OPEN) {
		my ($version, $as, $hold_time, $bgp_id, $params)
			= unpack('C n n a4 C/a', $data);
		# die if $version != 4;
		print "BGP PACKET TYPE: OPEN\n"
			. "AS: $as  ID: " . inet_ntoa($bgp_id) . "\n"
			. "HOLD TIME: ${hold_time}s\n";

		# parse BGP OPEN parameters
		while (length $params > 0) {
			my ($par_type, $par_value);
			($par_type, $par_value, $params) = unpack('C C/a a*', $params);
			if ($par_type == 1) {
				my ($code, $data) = unpack('C a*', $par_value);
				print "PARAMETER: AUTH code $code\n";
			} elsif ($par_type == 2) {
				my $caps = $par_value;
				while (length $caps > 0) {
					my ($cap_code, $cap_value);
					($cap_code, $cap_value, $caps) = unpack('C C/a a*', $caps);
					# see http://www.iana.org/assignments/capability-codes
					print "PARAMETER: CAPABILITY $cap_code\n";
				}
			} else {
				print "PARAMETER: TYPE $par_type (UNKNOWN)  "
					. "LEN: " . length($params) . "\n";
				hexdump($params);
			}
		}
	} elsif ($type == BGP_TYPE_UPDATE) {
		print "BGP PACKET TYPE: UPDATE\n";
		my ($unf_routes, $attributes, $nlri) = unpack('n/a n/a a*', $data);
		my $attr = parse_attributes($attributes);
		print_verbose_attributes($attr);
		print "WITHDRAWN: $_\n" foreach (parse_nlri_prefixes($unf_routes));
		print "ANNOUNCED: $_\n" foreach (parse_nlri_prefixes($nlri));
	} elsif ($type == BGP_TYPE_NOTIFICATION) {
		print "BGP PACKET TYPE: NOTIFICATION\n";
		my ($error, $suberror, $data) = unpack('C C a*', $data);
		print "BGP PACKET TYPE: ERROR $error (subcode $suberror)\n";
	} elsif ($type == BGP_TYPE_KEEPALIVE) {
		print "BGP PACKET TYPE: KEEPALIVE\n";
	} else { die }
}

sub parse_nlri_prefixes {
	my ($nlri, $afi) = @_;
	$afi ||= AFI_IP;

	my @prefixes;
	while ($nlri and length $nlri > 0) {
		my ($len, $prefix);
		($len, $nlri) = unpack('C a*', $nlri);
		my $bytes = int($len / 8) + ($len % 8 ? 1 : 0);
		($prefix, $nlri) = unpack("a$bytes a*", $nlri);
		$prefix .= "\0" x (($afi == AFI_IP ? 4 : 16) - $bytes); # pad with NULs
		push(@prefixes, inet_ntop($afi, $prefix) . "/$len");
	}
	return @prefixes;
}

sub print_verbose_attributes {
	my ($attr) = @_;

	print 'ORIGIN: ' . $BGP_ORIGIN[$attr->[BGP_ATTR_ORIGIN]] . "\n"
		if $attr->[BGP_ATTR_ORIGIN];
	print 'AS_PATH:'  . print_aspath($attr->[BGP_ATTR_AS_PATH]) . "\n"
		if $attr->[BGP_ATTR_AS_PATH];
	print 'NEXT_HOP: ' . inet_ntoa($attr->[BGP_ATTR_NEXT_HOP])."\n"
		if notnull($attr->[BGP_ATTR_NEXT_HOP]);
	print 'MULTI_EXIT_DISC: ' .  unpack('N', $attr->[BGP_ATTR_MULTI_EXIT_DISC])
		. "\n" if $attr->[BGP_ATTR_MULTI_EXIT_DISC];
	print "ATOMIC_AGGREGATE\n" if $attr->[BGP_ATTR_ATOMIC_AGGREGATE];
	print 'AGGREGATOR: ' . unpack('n', ${$attr->[BGP_ATTR_AGGREGATOR]}[0])
			. ' ' .  inet_ntoa(${$attr->[BGP_ATTR_AGGREGATOR]}[1]) . "\n"
		if $attr->[BGP_ATTR_AGGREGATOR];
	print "COMMUNITIES: "
			. print_communities(@{$attr->[BGP_ATTR_COMMUNITIES]}) . "\n"
		if $attr->[BGP_ATTR_COMMUNITIES];
	print "LARGE_COMMUNITIES: "
			. print_large_communities(@{$attr->[BGP_ATTR_LARGE_COMMUNITIES]}) . "\n"
		if $attr->[BGP_ATTR_LARGE_COMMUNITIES];
}

sub print_communities {
	my @communities;
	foreach my $community (@_) {
		my ($hi, $low) = unpack('n n', $community);
		push(@communities, "${hi}:${low}");
	}

	return join(' ', @communities);
}

sub print_large_communities {
	my @communities;
	foreach my $community (@_) {
		my ($ga, $ldp1, $ldp2) = unpack('N N N', $community);
		push(@communities, "${ga}:${ldp1}:${ldp2}");
	}

	return join(' ', @communities);
}

sub pretty_as {
	my ($as_hi, $as_lo) = unpack('nn', $_[0]);
	return defined $as_lo ? ($as_hi ? "$as_hi.$as_lo" : $as_lo) : $as_hi;
}

sub print_aspath {
	my ($aspath) = @_;

	my $s = '';
	foreach (@$aspath) {
		# 1 AS_SET  2 AS_SEQUENCE  3 AS_CONFED_SEQUENCE  4 AS_CONFED_SET
		my ($type, $segment) = @$_;
		my $s1 = $type == AS_SET ? '{' : '';
		my $s2 = $type == AS_SET ? '}' : '';
		my $s3 = $type == AS_SET ? ',' : ' ';
		$s .= " $s1" . join($s3, map { pretty_as($_) } @$segment) . $s2;
	}
	return $s;
}

sub origin_as {
	my ($aspath) = @_;

	# BEWARE: in presence of an AS_SET the first AS of the set is returned
	return pop @{ @{pop @{$aspath}}[1] };
}

sub notnull {
	return 1 if $_[0] and $_[0] ne "\0\0\0\0";
	return 0;
}

sub inet_ntop {
	my ($af, $addr) = @_;

	if ($af == AFI_IP) {
		return inet_ntoa($addr);
	} elsif ($af == AFI_IP6) {
		return inet6_ntoa($addr);
	} else { die }
}

sub inet_ntoa {
	join('.', unpack('C4', $_[0]));
}

sub inet6_ntoa {
	local $_ = sprintf("%0*v2x", ':', $_[0]);
	s/(..):(..)/${1}${2}/g;
	s/(:0000)+$/::/;
	return '::' if $_ eq '0000::';
	return $_;
}

sub hexdump {
	local $_ = sprintf("%0*v2X", ' ', $_[0]);
	s/((?:.. ){16})/${1}\n  /g;
	s/((?:.. ){8})/${1} /g;
	print "  $_\n";
}

