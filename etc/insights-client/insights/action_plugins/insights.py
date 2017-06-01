from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        remote_user = task_vars.get('ansible_ssh_user') or self._play_context.remote_user

        # copy our egg
        tmp = self._make_tmp_path(remote_user)
        source_full = self._loader.get_real_file("/usr/lib/python2.7/site-packages/insights-core.egg")
        tmp_src = self._connection._shell.join_path(tmp, 'insights')
        remote_path = self._transfer_file(source_full, tmp_src)
        results = merge_hash(results, self._execute_module(module_args={"egg_path": remote_path}, module_name="insights", tmp=tmp, task_vars=task_vars))
        return results
