insights_clientdir = $(pythondir)/insights_client

insights_client_PYTHON = \
	__init__.py \
	metrics.py \
	run.py \
	utc.py \
	$(NULL)

nodist_insights_client_PYTHON = \
	constants.py \
	$(NULL)

BUILT_SOURCES = \
	constants.py \
	$(NULL)

EXTRA_DIST = constants.py.in
CLEANFILES = constants.py

%: %.in Makefile
	$(AM_V_GEN) $(SED) \
		-e 's,[@]PACKAGE_VERSION[@],$(PACKAGE_VERSION),g' \
		-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
		-e 's,[@]PREFIX[@],$(prefix),g' \
		-e 's,[@]BINDIR[@],$(bindir),g' \
		-e 's,[@]SBINDIR[@],$(sbindir),g' \
		-e 's,[@]LIBEXECDIR[@],$(libexecdir),g' \
		-e 's,[@]DATAROOTDIR[@],$(datarootdir),g' \
		-e 's,[@]DATADIR[@],$(datadir),g' \
		-e 's,[@]SYSCONFDIR[@],$(sysconfdir),g' \
		-e 's,[@]LOCALSTATEDIR[@],$(localstatedir),g' \
		-e 's,[@]DOCDIR[@],$(docdir),g' \
		$< > $@.tmp && mv $@.tmp $@

SUBDIRS = tests

-include $(top_srcdir)/git.mk
