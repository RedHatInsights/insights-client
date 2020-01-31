SRCDIR=$(shell bash -c "pwd -P")
DISTDIR=$(SRCDIR)/dist
PKGNAME=insights-client
TARBALL=$(DISTDIR)/$(PKGNAME)-*.tar.gz
PY_SDIST=python setup.py sdist

.PHONY: tarball
tarball:
	@echo "'make tarball' is deprecated. Use 'make dist' instead."

.PHONY: dist
dist: $(TARBALL)
$(TARBALL): Makefile
	curl -o etc/.fallback.json https://api.access.redhat.com/r/insights/v1/static/core/uploader.json
	curl -o etc/.fallback.json.asc https://api.access.redhat.com/r/insights/v1/static/core/uploader.json.asc
	curl -o etc/rpm.egg https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg
	curl -o etc/rpm.egg.asc https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc
	$(PY_SDIST)

.PHONY: srpm 
srpm: $(SRPM)
$(SRPM): $(TARBALL) $(SPEC_FILE_IN)
	mkdir -p $(SRCDIR)/{RPMS,SPECS,SRPMS,SOURCES,BUILD,BUILDROOT}
	rpmbuild -ts --define="_topdir $(SRCDIR)" --define="_sourcedir dist" $(TARBALL)

.PHONY: rpm
rpm: $(RPM)
$(RPM): $(SRPM)
	rpmbuild --buildroot $(DISTDIR)/BUILDROOT --define="_topdir $(DISTDIR)" --rebuild $<

.PHONY: clean
clean:
	python setup.py clean --all
	rm -rf $(DISTDIR)
	rm etc/rpm.egg*