from betelgeuse import default_config

TESTCASE_CUSTOM_FIELDS = default_config.TESTCASE_CUSTOM_FIELDS + (
    "casecomponent",
    "requirement",
    "subsystemteam",
    "reference",
)

DEFAULT_CASECOMPONENT_VALUE = ""
DEFAULT_REQUIREMENT_VALUE = ""
DEFAULT_SUBSYSTEMTEAM_VALUE = ""
DEFAULT_REFERENCE_VALUE = ""
