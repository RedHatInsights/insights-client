from betelgeuse import default_config

TESTCASE_CUSTOM_FIELDS = default_config.TESTCASE_CUSTOM_FIELDS + (
    "component",
    "poolteam",
    "reference",
    "polarionincludeskipped",
    "polarionlookupmethod",
    "polarionprojectid",
)

DEFAULT_COMPONENT_VALUE = ""
DEFAULT_POOLTEAM_VALUE = ""
DEFAULT_REFERENCE_VALUE = ""
POLARION_INCLUDE_SKIPED = ""
POLARION_LOOKUP_METHOD = ""
POLARION_PROJECT_ID = ""
