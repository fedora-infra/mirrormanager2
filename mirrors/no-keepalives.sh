#!/bin/bash

path = 'pub/fedora/linux/releases/8/Fedora/i386/os'

[ "$1" != "" ] && path="$1"

tmpdir=$(mktemp -d /tmp/no-keepalives.XXXXXXXX) || exit 1
trap "rm -rf $tmpdir" EXIT QUIT HUP TERM

wget -q -O - "http://mirrors.fedoraproject.org/mirrorlist?country=global&path=$path" | grep http  > $tmpdir/mirrors
mkdir ${tmpdir}/hosts
for l in $(cat ${tmpdir}/mirrors); do
    host=$(echo $l | awk -F / '{print $3}') 
    wget -S -O /dev/null ${l}/GPL ${l}/GPL > ${tmpdir}/hosts/${host} 2>&1
done
for f in ${tmpdir}/hosts/*; do
    if ! grep -q ^Reusing $f; then
	echo $f
    fi
done
