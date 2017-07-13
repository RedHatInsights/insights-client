TOPDIR=$(shell bash -c "pwd -P")
RPMTOP=$(TOPDIR)/dist
PKGNAME=insights-client
SRPM=$(RPMTOP)/SRPMS/$(PKGNAME)-*.src.rpm
TARBALL=$(RPMTOP)/$(PKGNAME)-*.tar.gz
RPM=$(RPMTOP)/RPMS/noarch/$(PKGNAME)*.rpm
PY_SDIST=python setup.py sdist


all: rpm

.PHONY: tarball
tarball: $(TARBALL)
$(TARBALL): Makefile
	$(PY_SDIST)


.PHONY: srpm rpm 
srpm: $(SRPM)
$(SRPM): $(TARBALL) $(SPEC_FILE_IN)
	mkdir -p $(RPMTOP)/{RPMS,SPECS,SRPMS,SOURCES,BUILD,BUILDROOT}
	rpmbuild -ts --define="_topdir $(RPMTOP)" --define="_sourcedir dist" $(TARBALL)

.PHONY: rpm
rpm: $(RPM)
$(RPM): $(SRPM)
	rpmbuild --buildroot $(RPMTOP)/BUILDROOT --define="_topdir $(RPMTOP)" --rebuild $<

install: $(RPM)
	sudo yum install -y $(RPM)

clean:
	rm -rf dist
	rm -f MANIFEST
	rm -rf *.egg*
	find . -type f -name '*.pyc' -delete
