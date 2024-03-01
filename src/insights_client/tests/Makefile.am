dist_check_SCRIPTS = test_commands.py test_client.py test_sed.py


if HAVE_TEST
TESTS = pytest.sh
endif

pytest.sh: $(dist_check_SCRIPTS)
	echo 'PYTHONPATH=$(top_srcdir)/src:$(top_srcdir)/data/rpm.egg EGG=$(top_srcdir)/data/rpm.egg $(PYTEST) $(PYTEST_FLAGS) ./*.py' > $@
	chmod +x $@

CLEANFILES = pytest.sh
DISTCLEANFILES = __pycache__/*

clean-local:
	find . -name '.pytest_cache' -type d | xargs rm -fr

-include $(top_srcdir)/git.mk
