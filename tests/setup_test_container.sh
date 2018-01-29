#!/bin/bash -x

if [ $# -ne 1 ]; then
	echo "${0} requires distro name as parameter."
	exit 1
fi

echo "Installing for ${1}"

env

if [[ "${1}" == cento* ]]; then
	export PKG=yum
	export BUILDDEP=yum-builddep
else
	export PKG=dnf
	export BUILDDEP='dnf builddep'
fi

sudo docker exec `sed -e "s,:,-," <<< ${1}` \
	bash -c "if [[ \"${1}\" == cento* ]]; then \
		${PKG} -y install epel-release yum-utils; \
	else \
		${PKG} -y install dnf-plugins-core; \
	fi; \
	${PKG} -y install yum rsync rpm-build && \
	cd /tmp/test && \
	${BUILDDEP} -y utility/mirrormanager2.spec && \
	${PKG} -y install python2-mock python2-nose python-blinker python-nose python2-fedmsg-core; \
	${PKG} -y install python-coverage; \
	${PKG} -y install python2-coverage; \
	exit 0"

