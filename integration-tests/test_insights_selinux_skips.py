from insights_selinux import EXPECTED_SHADOW_FILE_DENIAL, avc_skips_for_test


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
