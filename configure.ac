AC_PREREQ(2.63)
AC_INIT([Insights Client], [m4_esyscmd_s([cat VERSION])])
AM_INIT_AUTOMAKE([1.11 foreign])
AC_CONFIG_MACRO_DIR([m4])
AM_SILENT_RULES([yes])

pkgsysconfdir=${sysconfdir}/$PACKAGE
AC_SUBST([pkgsysconfdir])

AC_PROG_SED
PKG_PROG_PKG_CONFIG
if test -z "$PKG_CONFIG"; then
    AC_MSG_ERROR([pkg-config is missing from your system...])
fi

AM_PATH_PYTHON([2.6])
AC_ARG_VAR([PYTEST], [the pytest test driver])
AC_ARG_VAR([PYTEST_FLAGS], [flags passed to pytest during check])

AC_PATH_PROG([WGET], [wget])
AS_IF([test -z "$WGET"],[
    AC_MSG_ERROR([wget is missing from your system...])
])
AC_PATH_PROG([TIMEOUT], [timeout])
AS_IF([test -z "$TIMEOUT"],[
    AC_MSG_ERROR([timeout is missing from your system...])
])
AC_PATH_PROGS([PYTEST], [pytest pytest-3 pytest3-6])
AS_IF([test -z "$PYTEST"],[
    AC_MSG_WARN([failed to find pytest, skipping tests...])
])
AM_CONDITIONAL([HAVE_PYTEST], [test x"$PYTEST" != x""])

if test ${TERM}x != x -a ${TERM} != dumb; then
    color () {
        tput setaf $1
    }
    reset () {
        tput sgr0
    }
else
    color () {
        :
    }
    reset () {
        :
    }
fi


AX_PYTHON_MODULE([six])
AS_IF([test x"$HAVE_PYMOD_SIX" = x"no"],[
    AC_MSG_WARN([$(color 1)missing python module: six$(reset)])
])
AX_PYTHON_MODULE([requests])
AS_IF([test x"$HAVE_PYMOD_REQUESTS" = x"no"],[
    AC_MSG_WARN([$(color 1)missing python module: requests$(reset)])
])
AX_PYTHON_MODULE([yaml])
AS_IF([test x"$HAVE_PYMOD_YAML" = x"no"],[
    AC_MSG_WARN([$(color 1)missing python module: yaml$(reset)])
])
AX_PYTHON_MODULE([rhsm])
AS_IF([test x"$HAVE_PYMOD_RHSM" = x"no"],[
    AC_MSG_WARN([$(color 1)missing python module: rhsm$(reset)])
])
AX_PYTHON_MODULE([mock])
AS_IF([test x"$HAVE_PYMOD_MOCK" = x"no"],[
    AC_MSG_WARN([$(color 1)missing python module: mock$(reset)])
])
AM_CONDITIONAL([HAVE_PYMOD_MOCK], [test x"$HAVE_PYMOD_MOCK" = x"yes"])

AM_CONDITIONAL([HAVE_TEST], [test x"$PYTEST" != x"" -a x"$HAVE_PYMOD_MOCK" = x"yes"])

dnl Set up required systemd directories and automake variables
SYSTEMD_SYSTEMUNITDIR
SYSTEMD_SYSTEMPRESETDIR

dnl Optionally install a systemd unit to automatically register insights-client
dnl when it detects an RHSM subscription.
AC_ARG_ENABLE([auto-registration],
    [AS_HELP_STRING([--enable-auto-registration],
        [enable automatic registration @<:@default: no@:>@])],
    [auto_registration=${enableval}], [auto_registration=no])
AM_CONDITIONAL([ENABLE_AUTO_REGISTRATION], [test "x${auto_registration}" = xyes])

dnl Optionally install a systemd unit to check-in hourly with the Inventory with
dnl a ultralight POST request.
AC_ARG_ENABLE([checkin],
    [AS_HELP_STRING([--enable-checkin],
        [enable hourly check-in @<:@default: no@:>@])],
    [checkin=${enableval}], [checkin=no])
AM_CONDITIONAL([ENABLE_CHECKIN], [test "x${checkin}" = xyes])

AC_CONFIG_FILES([
    Makefile
    data/Makefile
    data/cron/Makefile
    data/systemd/Makefile
    docs/Makefile
    src/Makefile
    src/insights_client/Makefile
    src/insights_client/tests/Makefile
])

AC_OUTPUT
