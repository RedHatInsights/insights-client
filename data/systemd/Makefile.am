dist_systemdsystemunit_DATA = \
	insights-client.service \
	insights-client.timer \
	insights-client-boot.service \
	$(NULL)

systemdsystemunit_DATA = \
	insights-client-results.service \
	insights-client-results.path \
	$(NULL)

systemdsystempreset_DATA = \
	$(NULL)

CLEANFILES = \
	insights-client-results.service \
	insights-client-results.path \
	$(NULL)

EXTRA_DIST = \
	insights-client-checkin.timer \
	insights-client-checkin.service.in \
	insights-client-results.service.in \
	insights-client-results.path.in \
	insights-register.service.in \
	insights-register.path.in \
	insights-unregister.service.in \
	insights-unregister.path.in \
	80-insights.preset \
	$(NULL)

if ENABLE_AUTO_REGISTRATION
systemdsystemunit_DATA += \
	insights-register.service \
	insights-register.path \
	insights-unregister.service \
	insights-unregister.path \
	$(NULL)
systemdsystempreset_DATA += \
	80-insights.preset \
	$(NULL)
CLEANFILES += \
	insights-register.service \
	insights-register.path \
	insights-unregister.service \
	insights-unregister.path \
	$(NULL)
endif

if ENABLE_CHECKIN
systemdsystemunit_DATA += \
	insights-client-checkin.timer \
	insights-client-checkin.service \
	$(NULL)
CLEANFILES += \
	insights-client-checkin.service \
	$(NULL)
endif

%: %.in Makefile
	$(AM_V_GEN) $(SED) \
		-e 's,[@]bindir[@],$(bindir),g' \
		-e 's,[@]pkgsysconfdir[@],$(pkgsysconfdir),g' \
		-e 's,[@]sysconfdir[@],$(sysconfdir),g' \
		$< > $@.tmp && mv $@.tmp $@

-include $(top_srcdir)/git.mk
