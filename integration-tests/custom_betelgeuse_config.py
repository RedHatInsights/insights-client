from betelgeuse import default_config

TESTCASE_CUSTOM_FIELDS = default_config.TESTCASE_CUSTOM_FIELDS + (
    "casecomponent",
    "subsystemteam",
    "reference",
)

DEFAULT_COMPONENT_VALUE = ""
DEFAULT_POOLTEAM_VALUE = ""
DEFAULT_REFERENCE_VALUE = ""
