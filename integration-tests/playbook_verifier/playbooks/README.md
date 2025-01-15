# Test data for the Ansible playbook verifier

To verify the functionality of the verifier, these playbooks have been downloaded from git repository of config-manager:
- [insights_setup.yml](https://github.com/RedHatInsights/config-manager/blob/master/playbooks/insights_setup.yml)
- [compliance_openscap_setup.yml](https://github.com/RedHatInsights/config-manager/blob/master/playbooks/compliance_openscap_setup.yml)

Additionally, this playbook has been downloaded from git repository of insights-ansible-playbook-verifier:
- [bugs.yml](https://github.com/RedHatInsights/insights-ansible-playbook-verifier/blob/main/data/playbooks/bugs.yml)

The list of playbooks should be extended to improve coverage:
- lines ending with Windows-style line endings (`\r\n`),
- comments with weird indentation,
- playbook with comments stripped before verifying,
- playbooks containing non-ASCII UTF-8 characters.
