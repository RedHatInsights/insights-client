pkgsysconfdir = $(sysconfdir)/insights-client

dist_pkgsysconf_DATA = \
	.exp.sed \
	.fallback.json \
	.fallback.json.asc \
	cert-api.access.redhat.com.pem \
	insights-client.conf \
	insights-client.motd \
	redhattools.pub.gpg \
	rpm.egg \
	rpm.egg.asc \
	$(NULL)

AM_V_DL = $(am__v_DL_$(V))
am__v_DL_ = $(am__v_DL_$(AM_DEFAULT_VERBOSITY))
am__v_DL_0 = @echo "  DL    " $@;

rpm.egg:
	$(AM_V_DL) $(WGET) --no-verbose --output-document $@ https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg

rpm.egg.asc:
	$(AM_V_DL) $(WGET) --no-verbose --output-document $@ https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc

CLEANFILES = rpm.egg rpm.egg.asc

if WITH_SYSTEMDSYSTEMUNITDIR
SYSTEMDDIR = systemd
else
CRONDIR = cron
endif

SUBDIRS = $(CRONDIR) $(SYSTEMDDIR)

-include $(top_srcdir)/git.mk
