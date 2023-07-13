#!/bin/bash -x

if [ $# -ne 1 ]; then
	echo "${0} requires distro name as parameter."
	exit 1
fi

echo "Installing for ${1}"

env

if [[ "${1}" == *cento* ]]; then
	export PKG="yum"
	export BUILDDEP="yum-builddep"
	${PKG} -y install epel-release yum-utils
else
	export PKG="dnf --best --allowerasing"
	export BUILDDEP="dnf builddep"
	${PKG} -y install dnf-plugins-core
fi

${PKG} -y install rsync rpm-build
${BUILDDEP} -y utility/mirrormanager2.spec
${PKG} -y install python3-blinker python3-pytest-cov python3-email-validator python3-flask
