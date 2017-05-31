#!/usr/bin/python
import sys
import json

def main():
    from ansible.module_utils.basic import AnsibleModule
    module = AnsibleModule({
        "egg_path": {"required": True, "type": "path"}
    })
    sys.path.append(module.params["egg_path"])
    import insights_core
    insights_core_json=insights_core.main()
    module.exit_json(insights_facts=insights_core_json)

if __name__ == "__main__":
    main()