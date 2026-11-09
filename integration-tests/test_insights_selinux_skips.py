from insights_selinux import (
    CONTAINER_FILE_SEARCH_DENIAL,
    EXPECTED_SHADOW_FILE_DENIAL,
    avc_skips_for_test,
)


def test_auditctl_skip_applies_to_all_insights_selinux_tests():
    expected = {
        "fields": {
            "subj": "system_u:system_r:auditctl_t:s0",
            "permission": "read",
            "obj": "system_u:object_r:auditd_log_t:s0",
        }
    }

    assert expected in avc_skips_for_test("test_register_unconfined_t_no_context_change")
    assert expected in avc_skips_for_test("test_selinux_core_context")


def test_cloud_what_cache_skip_applies_to_all_insights_tests():
    expected = {
        "fields": {
            "subj": "system_u:system_r:insights_core_t:s0",
            "syscall": "openat",
            "permission": "write",
            "obj": "unconfined_u:object_r:cloud_what_var_cache_t:s0",
        }
    }

    assert expected in avc_skips_for_test("test_register_with_ros")


def test_container_file_search_skip_matches_optional_mcs_categories():
    """Image-mode TF workdirs label container_file_t with MCS; exact field skips miss."""
    without_mcs = (
        "type=AVC msg=audit(01/01/26 00:00:00.000:1) : "
        "avc:  denied  { search } for  pid=1 comm=insights-client "
        "name=work-plansxxxxxx "
        "scontext=system_u:system_r:insights_client_t:s0 "
        "tcontext=system_u:object_r:container_file_t:s0 "
        "tclass=dir permissive=0"
    )
    with_mcs = (
        "type=AVC msg=audit(01/01/26 00:00:00.000:2) : "
        "avc:  denied  { search } for  pid=1 comm=insights-client "
        "name=work-plansxxxxxx "
        "scontext=system_u:system_r:insights_client_t:s0 "
        "tcontext=system_u:object_r:container_file_t:s0:c72,c422 "
        "tclass=dir permissive=0"
    )
    unrelated = (
        "type=AVC msg=audit(01/01/26 00:00:00.000:3) : "
        "avc:  denied  { write } for  pid=1 comm=insights-client "
        "name=insights-client.pid "
        "scontext=system_u:system_r:insights_client_t:s0 "
        "tcontext=system_u:object_r:var_run_t:s0 "
        "tclass=file permissive=0"
    )

    assert CONTAINER_FILE_SEARCH_DENIAL.search(without_mcs)
    assert CONTAINER_FILE_SEARCH_DENIAL.search(with_mcs)
    assert CONTAINER_FILE_SEARCH_DENIAL.search(unrelated) is None
    assert {"regex": CONTAINER_FILE_SEARCH_DENIAL} in avc_skips_for_test(
        "test_client_checkin_unregistered"
    )


def test_selinux_core_context_skips_are_test_scoped():
    ordinary_test_skips = avc_skips_for_test("test_register_unconfined_t_no_context_change")
    core_context_skips = avc_skips_for_test("test_selinux_core_context")

    core_only_fields = [
        {
            "subj": "system_u:system_r:insights_core_t:s0",
            "syscall": "write",
            "permission": "setfscreate",
            "obj": "system_u:system_r:insights_core_t:s0",
        },
        {
            "subj": "system_u:system_r:insights_core_t:s0",
            "syscall": "inotify_add_watch",
            "permission": "watch",
        },
    ]
    for fields in core_only_fields:
        assert {"fields": fields} not in ordinary_test_skips
        assert {"fields": fields} in core_context_skips

    assert {"regex": EXPECTED_SHADOW_FILE_DENIAL} not in ordinary_test_skips
    assert {"regex": EXPECTED_SHADOW_FILE_DENIAL} in core_context_skips
