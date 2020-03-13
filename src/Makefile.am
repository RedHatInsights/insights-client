SUBDIRS = insights_client

bin_SCRIPTS = insights-client
CLEANFILES = $(bin_SCRIPTS)
EXTRA_DIST = insights-client.in

%: %.in Makefile
	$(AM_V_GEN) $(SED) \
		-e 's,[@]pythondir[@],$(pythondir),g' \
		-e 's,[@]PYTHON[@],$(PYTHON),g' \
		$< > $@.tmp && mv $@.tmp $@
	chmod +x $@

-include $(top_srcdir)/git.mk
