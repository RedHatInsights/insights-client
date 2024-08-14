from betelgeuse import default_config

TESTCASE_CUSTOM_FIELDS = default_config.TESTCASE_CUSTOM_FIELDS + (
    "casecomponent",
    "requirement",
    "subsystemteam",
    "tier",
    "reference",
)

DEFAULT_CASECOMPONENT_VALUE = ""
DEFAULT_REQUIREMENT_VALUE = ""
DEFAULT_SUBSYSTEMTEAM_VALUE = ""
DEFAULT_TIER_VALUE = ""
DEFAULT_REFERENCE_VALUE = ""
