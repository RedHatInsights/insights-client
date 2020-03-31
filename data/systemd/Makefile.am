dist_systemdsystemunit_DATA = \
	insights-client.service \
	insights-client.timer \
	$(NULL)

systemdsystemunit_DATA = \
	insights-client-results.service \
	insights-client-results.path \
	$(NULL)

CLEANFILES = $(systemdsystemunit_DATA)
EXTRA_DIST = \
	insights-client-results.service.in \
	insights-client-results.path.in \
	$(NULL)

%: %.in Makefile
	$(AM_V_GEN) $(SED) \
		-e 's,[@]bindir[@],$(bindir),g' \
		-e 's,[@]pkgsysconfdir[@],$(pkgsysconfdir),g' \
		$< > $@.tmp && mv $@.tmp $@

-include $(top_srcdir)/git.mk
