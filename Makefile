TOPDIR=$(shell bash -c "pwd -P")
RPMTOP=$(TOPDIR)/dist
PKGNAME=insights-client
SRPM=$(RPMTOP)/SRPMS/$(PKGNAME)-*.src.rpm
TARBALL=$(RPMTOP)/$(PKGNAME)-*.tar.gz
RPM=$(RPMTOP)/RPMS/noarch/$(PKGNAME)*.rpm
OS_MAJOR_VER=$(shell python insights_client/major_version.py)
PY_SDIST=python setup.py sdist


all: rpm

.PHONY: tarball
tarball: $(TARBALL)
$(TARBALL): Makefile
	curl -o etc/.fallback.json https://api.access.redhat.com/r/insights/v1/static/core/uploader.json
	curl -o etc/.fallback.json.asc https://api.access.redhat.com/r/insights/v1/static/core/uploader.json.asc
	curl -o etc/rpm.egg https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg
	curl -o etc/rpm.egg.asc https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc
	if [ "$(OS_MAJOR_VER)" == "6" ]; then\
		cp MANIFEST.rhel6 MANIFEST.in;\
	else\
		cp MANIFEST.rhel7 MANIFEST.in;\
	fi
	$(PY_SDIST)
	rm MANIFEST.in


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
