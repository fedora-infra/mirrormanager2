RELEASE_DATE := "2-Dec-2008"
RELEASE_MAJOR := 1
RELEASE_MINOR := 2
RELEASE_EXTRALEVEL := .8
RELEASE_NAME := mirrormanager
RELEASE_VERSION := $(RELEASE_MAJOR).$(RELEASE_MINOR)$(RELEASE_EXTRALEVEL)
RELEASE_STRING := $(RELEASE_NAME)-$(RELEASE_VERSION)

SPEC=mirrormanager.spec
RELEASE_PY=server/mirrormanager/release.py
TARBALL=dist/$(RELEASE_STRING).tar.bz2
STARTSCRIPT=server/start-mirrormanager
PROGRAMDIR=/usr/share/mirrormanager/server
SBINDIR=/usr/sbin
.PHONY = all tarball prep

all:

clean:
	-rm -rf *.tar.gz *.rpm *~ dist/ $(SPEC) $(RELEASE_PY) server/mirrormanager.egg-info server/build

$(SPEC):
	sed -e 's/##VERSION##/$(RELEASE_VERSION)/' $(SPEC).in > $(SPEC)

$(RELEASE_PY):
	sed -e 's/##VERSION##/$(RELEASE_VERSION)/' $(RELEASE_PY).in > $(RELEASE_PY)

prep: $(SPEC) $(RELEASE_PY)
	pushd server; \
	python setup.py egg_info ;\
	sync ; sync ; sync

tarball: clean prep $(TARBALL)

$(TARBALL):
	sync ; sync ; sync
	mkdir -p dist
	tmp_dir=`mktemp -d /tmp/mirrormanager.XXXXXXXX` ; \
	cp -ar ../$(RELEASE_NAME) $${tmp_dir}/$(RELEASE_STRING) ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name .git -type d -exec rm -rf \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name dist -type d -exec rm -rf \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name fedora-test-data -type d -exec rm -rf \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name \*~ -type f -exec rm -f \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name \*.rpm -type f -exec rm -f \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name \*.tar.gz -type f -exec rm -f \{\} \; ; \
	sync ; sync ; sync ; \
	tar cvjf $(TARBALL) -C $${tmp_dir} $(RELEASE_STRING) ; \
	rm -rf $${tmp_dir} ;

rpm: tarball $(SPEC)
	tmp_dir=`mktemp -d` ; \
	mkdir -p $${tmp_dir}/{BUILD,RPMS,SRPMS,SPECS,SOURCES} ; \
	cp $(TARBALL) $${tmp_dir}/SOURCES ; \
	cp $(SPEC) $${tmp_dir}/SPECS ; \
	pushd $${tmp_dir} > /dev/null 2>&1; \
	rpmbuild -ba --define "_topdir $${tmp_dir}" SPECS/mirrormanager.spec ; \
	popd > /dev/null 2>&1; \
	cp $${tmp_dir}/RPMS/noarch/* $${tmp_dir}/SRPMS/* . ; \
	rm -rf $${tmp_dir} ; \
	rpmlint *.rpm

install: install-server install-client


install-server:
	mkdir -p -m 0755 $(DESTDIR)/var/lib/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/run/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/log/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/log/mirrormanager/crawler
	mkdir -p -m 0755 $(DESTDIR)/var/lock/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/usr/share/mirrormanager
# server/
	cp -ra server/	 $(DESTDIR)/usr/share/mirrormanager
	rm $(DESTDIR)/usr/share/mirrormanager/server/logrotate.conf
	rm $(DESTDIR)/usr/share/mirrormanager/server/*.cfg
	rm $(DESTDIR)/usr/share/mirrormanager/server/*.in
# mirrorlist-server/
	mkdir -p -m 0755 $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0755	mirrorlist-server/mirrorlist_client.wsgi $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0644	mirrorlist-server/weighted_shuffle.py $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0755	mirrorlist-server/mirrorlist_server.py $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0755	mirrorlist-server/mirrorlist_statistics.py $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	mkdir -p -m 0755 $(DESTDIR)/etc/httpd/conf.d
	install -m 0644 mirrorlist-server/apache/mirrorlist-server.conf $(DESTDIR)/etc/httpd/conf.d
# other junk
	mkdir -p -m 0755 $(DESTDIR)/etc/logrotate.d
	install -m 0644 server/logrotate.conf $(DESTDIR)/etc/logrotate.d/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/etc/mirrormanager
#	mkdir -p -m 0755 $(DESTDIR)/$(SBINDIR)
#	sed -e 's:##CONFFILE##:$(CONFFILE):' -e 's:##PROGRAMDIR##:$(PROGRAMDIR):' $(STARTSCRIPT).in > $(DESTDIR)/$(SBINDIR)/start-mirrormanager
#	chmod 0755 $(DESTDIR)/$(SBINDIR)/start-mirrormanager

install-client:
	mkdir -p -m 0755 $(DESTDIR)/etc/mirrormanager-client $(DESTDIR)/usr/bin
	install -m 0644 client/report_mirror.conf $(DESTDIR)/etc/mirrormanager-client/
	install -m 0755 client/report_mirror $(DESTDIR)/usr/bin/

sign: $(TARBALL)
	gpg --armor --detach-sign $(TARBALL)
	mv "$(TARBALL).asc" "`dirname $(TARBALL)`/`basename $(TARBALL) .asc`.sign"

publish: sign
	scp dist/* fedorahosted.org:/srv/web/releases/m/i/mirrormanager/
