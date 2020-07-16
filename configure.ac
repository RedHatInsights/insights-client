AC_PREREQ(2.63)
AC_INIT([Insights Client], [3.0.16])
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
AC_PATH_PROG([STRINGS], [strings])
AS_IF([test -z "$STRINGS"],[
    AC_MSG_ERROR([strings is missing from your system...])
])
AC_PATH_PROG([TIMEOUT], [timeout])
AS_IF([test -z "$TIMEOUT"],[
    AC_MSG_ERROR([timeout is missing from your system...])
])
AC_PATH_PROG([PYTEST], [pytest])
AS_IF([test -z "$PYTEST"],[
    AC_MSG_WARN([failed to find pytest, skipping tests...])
])
AM_CONDITIONAL([HAVE_PYTEST], [test x"$PYTEST" != x""])

AX_PYTHON_MODULE([six])
AS_IF([test x"$HAVE_PYMOD_SIX" = x"no"],[
    AC_MSG_WARN([missing python module: six])
])
AX_PYTHON_MODULE([requests])
AS_IF([test x"$HAVE_PYMOD_REQUESTS" = x"no"],[
    AC_MSG_WARN([missing python module: requests])
])
AX_PYTHON_MODULE([yaml])
AS_IF([test x"$HAVE_PYMOD_YAML" = x"no"],[
    AC_MSG_WARN([missing python module: yaml])
])
AX_PYTHON_MODULE([rhsm])
AS_IF([test x"$HAVE_PYMOD_RHSM" = x"no"],[
    AC_MSG_WARN([missing python module: rhsm])
])

dnl Set up required systemd directories and automake variables
SYSTEMD_SYSTEMUNITDIR
SYSTEMD_SYSTEMPRESETDIR

dnl Check for version of pam_motd.so that supports motd.d.
dnl This is ugly but seems to be the most reliable way to detect which version
dnl of PAM is available on the system.
AC_MSG_CHECKING([for motd_d support])
have_motdd=no
if test -f $libdir/security/pam_motd.so; then
    $STRINGS $libdir/security/pam_motd.so | grep -q "motd_dir="
    if test $? -eq 0; then
        have_motdd=yes
    fi
fi
AC_MSG_RESULT([$have_motdd])
AM_CONDITIONAL([HAVE_MOTDD], [test x"$have_motdd" = x"yes"])

dnl Optionally install a systemd unit to automatically register insights-client
dnl when it detects an RHSM subscription.
AC_ARG_ENABLE([auto-registration],
    [AS_HELP_STRING([--enable-auto-registration],
        [enable automatic registration @<:@default: no@:>@])],
    [auto_registration=${enableval}], [auto_registration=no])
AM_CONDITIONAL([ENABLE_AUTO_REGISTRATION], [test "x${auto_registration}" = xyes])

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
