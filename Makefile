SRCDIR=$(shell bash -c "pwd -P")
BUILDDIR=$(SRCDIR)/build
DISTDIR=$(SRCDIR)/dist
PKGNAME=insights-client
TARBALL=$(DISTDIR)/$(PKGNAME)-*.tar.gz
PY_SDIST=python setup.py sdist
PY_CLEAN=python setup.py clean

.PHONY: tarball
tarball:
	@echo "'make tarball' is deprecated. Use 'make dist' instead."

.PHONY: dist
dist: $(TARBALL)
$(TARBALL):
	$(PY_SDIST)

.PHONY: clean
clean:
	$(PY_CLEAN)
