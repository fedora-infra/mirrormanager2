RELEASE_DATE := "26-Sep-2008"
RELEASE_MAJOR := 1
RELEASE_MINOR := 2
RELEASE_EXTRALEVEL := .2
RELEASE_NAME := mirrormanager
RELEASE_VERSION := $(RELEASE_MAJOR).$(RELEASE_MINOR)$(RELEASE_EXTRALEVEL)
RELEASE_STRING := $(RELEASE_NAME)-$(RELEASE_VERSION)

SPEC=mirrormanager.spec
RELEASE_PY=mirrors/mirrors/release.py

.PHONY = all tarball

all:

clean:
	-rm -rf *.tar.gz *.rpm *~ dist/ $(SPEC) $(RELEASE_PY)

$(SPEC):
	sed -e 's/##VERSION##/$(RELEASE_VERSION)/' $(SPEC).in > $(SPEC)

$(RELEASE_PY):
	sed -e 's/##VERSION##/$(RELEASE_VERSION)/' $(RELEASE_PY).in > $(RELEASE_PY)


TARBALL=dist/$(RELEASE_STRING).tar.bz2

tarball: $(SPEC) $(RELEASE_PY) $(TARBALL)

$(TARBALL):
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

install: install-server install-client

install-server:
	mkdir -p -m 0755 $(DESTDIR)/var/lib/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/run/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/log/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/var/lock/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/usr/share/mirrormanager
	cp -ra mirrors/	 $(DESTDIR)/usr/share/mirrormanager
	rm $(DESTDIR)/usr/share/mirrormanager/mirrors/logrotate.conf
	mkdir -p -m 0755 $(DESTDIR)/etc/logrotate.d
	install -m 0644 mirrors/logrotate.conf $(DESTDIR)/etc/logrotate.d/mirrormanager
	mkdir -p -m 0755 $(DESTDIR)/etc/mirrormanager

install-client:
	mkdir -p -m 0755 $(DESTDIR)/etc/mirrormanager-client $(DESTDIR)/usr/bin
	install -m 0644 client/report_mirror.conf $(DESTDIR)/etc/mirrormanager-client/
	install -m 0755 client/report_mirror $(DESTDIR)/usr/bin/
