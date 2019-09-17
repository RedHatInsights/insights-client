import subprocess

from subprocess import PIPE


def run_insights_client_run():
    '''
    Run the run.py script and test that it errors out.
    '''
    output = subprocess.Popen(['python', '../run.py'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = output.communicate()

    return (output, stderr)


def test_script_exit_code():
    (output, stderr) = run_insights_client_run()

    assert output.returncode != 0


def test_script_error_check():
    (output, stderr) = run_insights_client_run()

    assert stderr is not None
