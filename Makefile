BUILDROOT ?=
BINDIR ?= /usr/bin
PYTHON3_SITELIB ?= /usr/lib/python3.12/site-packages
SYSCONFDIR ?= /etc
UNITDIR ?= /usr/lib/systemd/system
PRESETDIR ?= /usr/lib/systemd/system-preset
TMPFILESDIR ?= /usr/lib/tmpfiles.d
MANDIR ?= /usr/share/man
DEFAULTDOCDIR ?= /usr/share/doc
LOCALSTATEDIR ?= /var
NAME ?= insights-client

.PHONY: install-files
install-files:
	# ./src/ -> /usr/bin/
	install -d -m 755 "$(BUILDROOT)$(BINDIR)/"
	install -m 755 src/insights-client "$(BUILDROOT)$(BINDIR)/"

	# ./src/insights_client/ -> /usr/lib/python3.12/site-packages/insights_client/
	install -d -m 755 "$(BUILDROOT)$(PYTHON3_SITELIB)/insights_client/"
	cp -pr src/insights_client/* "$(BUILDROOT)$(PYTHON3_SITELIB)/insights_client/"
	rm -rf "$(BUILDROOT)$(PYTHON3_SITELIB)/insights_client/tests/"
	rm -f "$(BUILDROOT)$(PYTHON3_SITELIB)/insights_client/constants.py.in"

	# ./data/etc/ -> /etc/insights-client/
	install -d -m 755 "$(BUILDROOT)$(SYSCONFDIR)/insights-client/"
	install -m 644 data/etc/cert-api.access.redhat.com.pem "$(BUILDROOT)$(SYSCONFDIR)/insights-client/cert-api.access.redhat.com.pem"
	install -m 644 data/etc/insights-client.conf "$(BUILDROOT)$(SYSCONFDIR)/insights-client/insights-client.conf"
	install -m 644 data/etc/insights-client.motd "$(BUILDROOT)$(SYSCONFDIR)/insights-client/insights-client.motd"

	# ./data/logrotate.d/ -> /etc/logrotate.d/
	install -d -m 755 "$(BUILDROOT)$(SYSCONFDIR)/logrotate.d/"
	install -m 644 data/logrotate.d/insights-client "$(BUILDROOT)$(SYSCONFDIR)/logrotate.d/insights-client"

	# ./data/systemd/ -> /usr/lib/systemd/system/
	install -d -m 755 "$(BUILDROOT)$(UNITDIR)/"
	install -m 644 data/systemd/insights-client* "$(BUILDROOT)$(UNITDIR)/"

	# ./data/systemd/ -> /usr/lib/systemd/system-preset/
	install -d -m 755 "$(BUILDROOT)$(PRESETDIR)/"
	install -m 644 data/systemd/80-insights.preset "$(BUILDROOT)$(PRESETDIR)/80-insights.preset"

	# ./data/tmpfiles.d/ -> /usr/lib/tmpfiles.d/
	install -d -m 755 "$(BUILDROOT)$(TMPFILESDIR)/"
	install -m 644 data/tmpfiles.d/insights-client.conf "$(BUILDROOT)$(TMPFILESDIR)/insights-client.conf"

	# ./docs/ -> /usr/share/man/man8/
	install -d -m 755 "$(BUILDROOT)$(MANDIR)/man8/"
	install -m 644 docs/insights-client.8 "$(BUILDROOT)$(MANDIR)/man8/"

	# ./docs/ -> /usr/share/man/man5/
	install -d -m 755 "$(BUILDROOT)$(MANDIR)/man5/"
	install -m 644 docs/insights-client.conf.5 "$(BUILDROOT)$(MANDIR)/man5/"

	# ./docs/ -> /usr/share/doc/insights-client/
	install -d -m 755 "$(BUILDROOT)$(DEFAULTDOCDIR)/$(NAME)/"
	install -m 644 docs/file-redaction.yaml.example "$(BUILDROOT)$(DEFAULTDOCDIR)/$(NAME)/"
	install -m 644 docs/file-content-redaction.yaml.example "$(BUILDROOT)$(DEFAULTDOCDIR)/$(NAME)/"

	# Create different insights directories in /var
	install -d -m 755 "$(BUILDROOT)$(LOCALSTATEDIR)/log/insights-client/"
	install -d -m 755 "$(BUILDROOT)$(LOCALSTATEDIR)/lib/insights/"
	install -d -m 755 "$(BUILDROOT)$(LOCALSTATEDIR)/cache/insights/"
	install -d -m 755 "$(BUILDROOT)$(LOCALSTATEDIR)/cache/insights-client/"

.PHONY: install-auto-registration-files
install-auto-registration-files:
	# ./data/systemd/systemd-autoregistration/ -> /usr/lib/systemd/system/
	install -m 644 data/systemd/systemd-autoregistration/* "$(BUILDROOT)$(UNITDIR)/"

.PHONY: install-checkin-files
install-checkin-files:
	# ./data/systemd/systemd-checkin/ -> /usr/lib/systemd/system/
	install -m 644 data/systemd/systemd-checkin/* "$(BUILDROOT)$(UNITDIR)/"
