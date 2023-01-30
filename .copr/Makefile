CUR_VERSION := $(shell cat VERSION)
NEXT_VERSION := $(shell echo $(CUR_VERSION) | awk -F. '{printf("%d.%d.%d", $$1, $$2, $$3+1)}')

srpm:
	dnf install -y automake autoconf wget git systemd
	echo $(NEXT_VERSION) > VERSION
	./autogen.sh
	echo $(CUR_VERSION) > VERSION
	make dist
	sed -e "s/@PACKAGE_VERSION@/$(NEXT_VERSION)/g" -e "s/@COMMIT_HASH@/$$(git --no-pager log --pretty=tformat:"%h" -n 1)/g" $(spec).in > $(spec)
	rpmbuild -bs $(spec) --define '_topdir .copr' --define '_sourcedir .'
	mv .copr/SRPMS/insights-client-*.src.rpm $(outdir)
