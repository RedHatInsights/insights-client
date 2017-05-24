TOPDIR=$(shell bash -c "pwd -P")
RPMTOP=$(TOPDIR)/dist
PKGNAME=insights-client
SRPM=$(RPMTOP)/SRPMS/$(PKGNAME)-*.src.rpm
TARBALL=$(RPMTOP)/$(PKGNAME)-*.tar.gz
RPM=$(RPMTOP)/RPMS/noarch/$(PKGNAME)*.rpm
SPECFILE=insights-client.spec



all: rpm


.PHONY: rpm
rpm: $(RPM)
$(RPM):
	mkdir -p $(RPMTOP)/{RPMS,SPECS,SRPMS,SOURCES,BUILD,BUILDROOT}
	rpmbuild -ba --buildroot $(RPMTOP)/BUILDROOT --define="_topdir $(RPMTOP)" --define="_sourcedir $(TOPDIR)" $(SPECFILE)

install: $(RPM)
	sudo dnf install -y $(RPM)

clean:
	rm -rf dist build *.egg-info
	find . -type f -name '*.pyc' -delete

egg:
	python setup.py bdist_egg
