SRCDIR=$(shell bash -c "pwd -P")
BUILDDIR=$(SRCDIR)/build
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
	$(PY_SDIST)

.PHONY: clean
clean:
	python setup.py clean --all
	rm -rf $(DISTDIR)
	rm -rf $(BUILDDIR)
	rm etc/rpm.egg*
