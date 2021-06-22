SUBDIRS = insights_client

bin_SCRIPTS = \
	insights-client \
	redhat-access-insights \
	$(NULL)
CLEANFILES = $(bin_SCRIPTS)
EXTRA_DIST = \
	insights-client.in \
	redhat-access-insights.in \
	$(NULL)

%: %.in Makefile
	$(AM_V_GEN) $(SED) \
		-e 's,[@]bindir[@],$(bindir),g' \
		-e 's,[@]pythondir[@],$(pythondir),g' \
		-e 's,[@]PYTHON[@],$(PYTHON),g' \
		$< > $@.tmp && mv $@.tmp $@
	chmod +x $@

-include $(top_srcdir)/git.mk
