CUR_VERSION := $(shell cat VERSION)
NEXT_VERSION := $(shell echo $(CUR_VERSION) | awk -F. '{printf("%d.%d.%d", $$1, $$2, $$3+1)}')
COMMIT := $(shell git --no-pager log --pretty=tformat:"%h" -n 1)

srpm:
	dnf install -y meson curl git rpmdevtools systemd
	meson setup --wipe --reconfigure builddir
	meson dist --no-tests -C builddir
	cp builddir/meson-dist/insights-client-*.tar.xz .
	rpmdev-bumpspec --string=git.$(COMMIT) $(spec)
	rpmbuild -bs $(spec) --define '_topdir .copr' --define '_sourcedir .'
	mv .copr/SRPMS/insights-client-*.src.rpm $(outdir)
