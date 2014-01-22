RELEASE_DATE := "21-Jan-2014"
RELEASE_MAJOR := 1
RELEASE_MINOR := 4
RELEASE_EXTRALEVEL := .4
RELEASE_NAME := mirrormanager
RELEASE_VERSION := $(RELEASE_MAJOR).$(RELEASE_MINOR)$(RELEASE_EXTRALEVEL)
RELEASE_STRING := $(RELEASE_NAME)-$(RELEASE_VERSION)

SPEC=mirrormanager.spec
RELEASE_PY=server/mirrormanager/release.py
TARBALL=dist/$(RELEASE_STRING).tar.xz
STARTSCRIPT=server/start-mirrormanager
PROGRAMDIR=/usr/share/mirrormanager/server
SBINDIR=/usr/sbin
.PHONY = all tarball prep

all:

clean:
	-rm -rf *.tar.xz *.rpm *~ dist/ $(SPEC) $(RELEASE_PY) server/mirrormanager.egg-info server/build
	-find . -name \*.pyc -exec rm \{\} \;
	-find . -name \*.pyo -exec rm \{\} \;

$(SPEC):
	sed -e 's/##VERSION##/$(RELEASE_VERSION)/' $(SPEC).in > $(SPEC)

$(RELEASE_PY):
	sed -e 's/##VERSION##/$(RELEASE_VERSION)/' $(RELEASE_PY).in > $(RELEASE_PY)

prep: $(SPEC) $(RELEASE_PY)
	cd server ; python setup.py egg_info
	echo 'db_module=mirrormanager.model' > server/mirrormanager.egg-info/sqlobject.txt
#	echo 'history_dir=$$base/mirrormanager/sqlobject-history' >> server/mirrormanager.egg-info/sqlobject.txt
	sync ; sync ; sync

tarball: clean prep $(TARBALL)

$(TARBALL):
	sync ; sync ; sync
	mkdir -p dist
	tmp_dir=`mktemp -d /tmp/mirrormanager.XXXXXXXX` ; \
	cp -ar ../$(RELEASE_NAME) $${tmp_dir}/$(RELEASE_STRING) ; \
	rm $${tmp_dir}/$(RELEASE_STRING)/.gitignore ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name .git -type d -exec rm -rf \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name dist -type d -exec rm -rf \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name fedora-test-data -type d -exec rm -rf \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name sqlobject-history -type d -exec rm -rf \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name \*~ -type f -exec rm -f \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name \*.rpm -type f -exec rm -f \{\} \; ; \
	find $${tmp_dir}/$(RELEASE_STRING) -depth -name \*.tar.xz -type f -exec rm -f \{\} \; ; \
	sync ; sync ; sync ; \
	tar cv -C $${tmp_dir} $(RELEASE_STRING) | xz -c -9 > $(TARBALL); \
	rm -rf $${tmp_dir} ;

# Use older digest algorithms for local rpmbuilds, as EPEL5 and
# earlier releases need this.  When building using mock for a
# particular target, it will use the proper (newer) digests if that
# target supports it.
rpm: tarball $(SPEC)
	tmp_dir=`mktemp -d` ; \
	mkdir -p $${tmp_dir}/{BUILD,RPMS,SRPMS,SPECS,SOURCES} ; \
	cp $(TARBALL) $${tmp_dir}/SOURCES ; \
	cp $(SPEC) $${tmp_dir}/SPECS ; \
	cd $${tmp_dir} > /dev/null 2>&1; \
	rpmbuild -ba --define "_topdir $${tmp_dir}" \
	  --define "_source_filedigest_algorithm 0" \
	  --define "_binary_filedigest_algorithm 0" \
	  --define "dist %{nil}" \
          SPECS/mirrormanager.spec ; \
	cd - > /dev/null 2>&1; \
	cp $${tmp_dir}/RPMS/noarch/* $${tmp_dir}/SRPMS/* . ; \
	rm -rf $${tmp_dir} ; \
	rpmlint *.rpm *.spec

install: install-server install-client


install-server:
	mkdir -p -m 0755 $(DESTDIR)/var/lib/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/lib/mirrormanager/catwalk-session
	mkdir -p -m 0755 $(DESTDIR)/var/run/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/log/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/log/mirrormanager/crawler
	mkdir -p -m 0755 $(DESTDIR)/var/lock/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/usr/share/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/etc/httpd/conf.d
	mkdir -p -m 0755 $(DESTDIR)/etc/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/etc/rpmlint
	mkdir -p -m 0755 $(DESTDIR)/etc/tmpfiles.d
# server/
	cp -ra server/	 $(DESTDIR)/usr/share/mirrormanager
	install -m 0644 server/apache/mirrormanager.conf $(DESTDIR)/etc/httpd/conf.d
	install -m 0644 server/prod.cfg.example  $(DESTDIR)/etc/mirrormanager/prod.cfg
	install -m 0644 rpmlint-mirrormanager.config  $(DESTDIR)/etc/rpmlint/mirrormanager.config
	rm $(DESTDIR)/usr/share/mirrormanager/server/prod.cfg.example
	rm $(DESTDIR)/usr/share/mirrormanager/server/logrotate.conf
	rm $(DESTDIR)/usr/share/mirrormanager/server/*.cfg
	rm $(DESTDIR)/usr/share/mirrormanager/server/*.in
# mirrorlist-server/
	mkdir -p -m 0755 $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0755	mirrorlist-server/mirrorlist_client.wsgi $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0644	mirrorlist-server/weighted_shuffle.py $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0755	mirrorlist-server/mirrorlist_server.py $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
	install -m 0755	mirrorlist-server/mirrorlist_statistics.py $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server
# mirrorlist-server/test
	mkdir -p -m 0755 $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server/test
	install -m 0755	mirrorlist-server/test/induce-stress $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server/test/induce-stress
	install -m 0755	mirrorlist-server/test/server_tester.py $(DESTDIR)/usr/share/mirrormanager/mirrorlist-server/test/server_tester.py
# apache
	mkdir -p -m 0755 $(DESTDIR)/etc/httpd/conf.d
	install -m 0644 mirrorlist-server/apache/mirrorlist-server.conf $(DESTDIR)/etc/httpd/conf.d
	mkdir -p -m 0755 $(DESTDIR)/etc/supervisord.d
	install -m 0644 mirrorlist-server/supervisor/mirrorlist-server.ini $(DESTDIR)/etc/supervisord.d
# other junk
	mkdir -p -m 0755 $(DESTDIR)/etc/logrotate.d
	install -m 0644 server/logrotate.conf $(DESTDIR)/etc/logrotate.d/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/etc/mirrormanager
#	mkdir -p -m 0755 $(DESTDIR)/$(SBINDIR)
#	sed -e 's:##CONFFILE##:$(CONFFILE):' -e 's:##PROGRAMDIR##:$(PROGRAMDIR):' $(STARTSCRIPT).in > $(DESTDIR)/$(SBINDIR)/start-mirrormanager
#	chmod 0755 $(DESTDIR)/$(SBINDIR)/start-mirrormanager
	install -m 0644 mirrormanager.tmpfiles $(DESTDIR)/etc/tmpfiles.d/mirrormanager.conf

install-client:
	mkdir -p -m 0755 $(DESTDIR)/etc/mirrormanager-client $(DESTDIR)/usr/bin
	install -m 0644 client/report_mirror.conf $(DESTDIR)/etc/mirrormanager-client/
	install -m 0755 client/report_mirror $(DESTDIR)/usr/bin/

sign: $(TARBALL)
	gpg --armor --detach-sign $(TARBALL)
	mv "$(TARBALL).asc" "`dirname $(TARBALL)`/`basename $(TARBALL) .asc`.sign"

publish: sign
	scp dist/* fedorahosted.org:/srv/web/releases/m/i/mirrormanager/

git-sign-push:
	git tag -s -m v$(RELEASE_VERSION) v$(RELEASE_VERSION)
	git push
	git push --tags

schema:
	mkdir -p dist/schema_docs
	java -jar schemaSpy_5.0.0.jar -t mysql -host localhost -db mirrormanager -u mirrormanager -p mirrormanager -o dist/schema_docs/ -dp /usr/share/java/mysql-connector-java-5.1.22.jar
