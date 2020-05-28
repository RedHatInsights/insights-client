dist_systemdsystemunit_DATA = \
	insights-client.service \
	insights-client.timer \
	$(NULL)

systemdsystemunit_DATA = \
	insights-client-results.service \
	insights-client-results.path \
	insights-register.service \
	insights-register.path \
	$(NULL)

CLEANFILES = $(systemdsystemunit_DATA)
EXTRA_DIST = \
	insights-client-results.service.in \
	insights-client-results.path.in \
	insights-register.service.in \
	insights-register.path.in \
	$(NULL)

%: %.in Makefile
	$(AM_V_GEN) $(SED) \
		-e 's,[@]bindir[@],$(bindir),g' \
		-e 's,[@]pkgsysconfdir[@],$(pkgsysconfdir),g' \
		-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
		$< > $@.tmp && mv $@.tmp $@

-include $(top_srcdir)/git.mk
