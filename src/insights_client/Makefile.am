insights_clientdir = $(pythondir)/insights_client

insights_client_PYTHON = \
	__init__.py \
	run.py \
	$(NULL)

nodist_insights_client_PYTHON = \
	constants.py \
	$(NULL)

EXTRA_DIST = constants.py.in
CLEANFILES = constants.py

%: %.in Makefile
	$(AM_V_GEN) $(SED) \
		-e 's,[@]PACKAGE_VERSION[@],$(PACKAGE_VERSION),g' \
		-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
		$< > $@.tmp && mv $@.tmp $@

SUBDIRS = tests

-include $(top_srcdir)/git.mk
