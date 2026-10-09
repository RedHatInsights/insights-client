"""Insights-client's known SELinux AVC exceptions."""

import re

EXPECTED_SHADOW_FILE_DENIAL = re.compile(
    r"^type=AVC .* avc:  denied  { unlink } for .* "
    r'name=(?:"\.registered"|\.registered) .* '
    r"scontext=system_u:system_r:insights_core_t:s0 "
    r"tcontext=unconfined_u:object_r:shadow_t:s0 "
    r"tclass=file permissive=1\b",
    flags=re.MULTILINE,
)
# This is the deliberate denial asserted by test_selinux_core_context.
# https://redhat.atlassian.net/browse/CCT-1719


_KNOWN_AVC_SKIPS = [
    {
        "fields": {
            "subj": "system_u:system_r:auditctl_t:s0",
            "permission": "read",
            "obj": "system_u:object_r:auditd_log_t:s0",
        }
    },  # RHEL 10 only: https://redhat.atlassian.net/browse/RHEL-246545
    {
        "fields": {
            "subj": "system_u:system_r:insights_client_t:s0",
            "syscall": "openat",
            "permission": "search",
            "obj": "unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023",
        }
    },  # https://redhat.atlassian.net/browse/CCT-2009
    {
        "fields": {
            "subj": "system_u:system_r:insights_client_t:s0",
            "syscall": "fstat",
            "permission": "getattr",
            "obj": "unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023",
        }
    },  # aarch64 uses newfstat; https://redhat.atlassian.net/browse/CCT-2009
    {
        "fields": {
            "subj": "system_u:system_r:insights_client_t:s0",
            "syscall": "newfstat",
            "permission": "getattr",
            "obj": "unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023",
        }
    },  # https://redhat.atlassian.net/browse/CCT-2009
    {
        "fields": {
            "subj": "system_u:system_r:rhsmcertd_t:s0",
            "syscall": "openat",
            "permission": "read",
            "obj": "unconfined_u:object_r:admin_home_t:s0",
        }
    },  # https://redhat.atlassian.net/browse/TFT-4293
    {
        "fields": {
            "subj": "system_u:system_r:insights_client_t:s0",
            "permission": "search",
            "obj": "system_u:object_r:container_file_t:s0",
        }
    },  # https://redhat.atlassian.net/browse/TFT-4293
    {
        "fields": {
            "subj": "system_u:system_r:insights_client_t:s0",
            "permission": "write",
            "obj": "system_u:object_r:var_run_t:s0",
        }
    },  # RHEL 10 only: https://redhat.atlassian.net/browse/RHEL-247146
    {
        "fields": {
            "subj": "system_u:system_r:insights_core_t:s0",
            "syscall": "openat",
            "permission": "write",
            "obj": "unconfined_u:object_r:cloud_what_var_cache_t:s0",
        }
    },  # https://redhat.atlassian.net/browse/RHEL-180919
]

_SELINUX_CORE_CONTEXT_SKIPS = [
    {
        "fields": {
            "subj": "system_u:system_r:insights_client_t:s0",
            "syscall": "openat",
            "obj": "unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023",
        }
    },  # https://redhat.atlassian.net/browse/CCT-2009
    {
        "fields": {
            "subj": "system_u:system_r:insights_core_t:s0",
            "syscall": "write",
            "permission": "setfscreate",
            "obj": "system_u:system_r:insights_core_t:s0",
        }
    },  # https://redhat.atlassian.net/browse/RHEL-146146
    {
        "fields": {
            "subj": "system_u:system_r:insights_core_t:s0",
            "syscall": "inotify_add_watch",
            "permission": "watch",
        }
    },  # https://redhat.atlassian.net/browse/RHEL-146146
    {"regex": EXPECTED_SHADOW_FILE_DENIAL},
]


def avc_skips_for_test(test_name):
    """Return Insights-client skip rules applicable to this test."""
    skips = list(_KNOWN_AVC_SKIPS)
    if test_name == "test_selinux_core_context":
        skips.extend(_SELINUX_CORE_CONTEXT_SKIPS)
    return skips
