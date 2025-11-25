import re
import subprocess
from datetime import datetime


def _parse_execve_event_block(event_lines):
    """
    Parse a block of audit lines (one event) to extract process info.
    Correlates SYSCALL (context) with EXECVE (full arguments).
    """
    # Join lines to make searching easier, or iterate
    full_text = "\n".join(event_lines)

    # 1. Extract contexts from SYSCALL
    # scontext = subject context (parent process that executed)
    scontext_match = re.search(r"(?:subj|scontext)=([^\s]+)", full_text)
    if not scontext_match:
        return None
    scontext = scontext_match.group(1)

    # tcontext = target context (file being executed)
    # newcontext = actual running context if setexeccon was used
    newcontext_match = re.search(r"newcontext=([^\s]+)", full_text)
    tcontext_match = re.search(r"tcontext=([^\s]+)", full_text)

    # Running context is newcontext if setexeccon was used, otherwise tcontext
    if newcontext_match:
        running_context = newcontext_match.group(1)
    elif tcontext_match:
        running_context = tcontext_match.group(1)
    else:
        # Fallback to scontext if neither found (shouldn't happen normally)
        running_context = scontext

    # 2. Extract Command/Arguments from EXECVE
    if "type=EXECVE" not in full_text:
        return None

    # Extract all arguments to reconstruct the command roughly
    args = re.findall(r'a\d+=(?:"([^"]+)"|([^\s]+))', full_text)
    cmd_args = [x[0] or x[1] for x in args]
    cmd_string = " ".join(cmd_args)

    # 3. Filter: Is this the process we care about?
    # We only care if the arguments mention insights-client structure
    target_markers = ["insights-client", "insights_client", "insights-core", "run.py"]
    if not any(marker in cmd_string for marker in target_markers):
        return None
    # Comm is usually the base command (first arg or explicit comm field)
    comm_match = re.search(r'comm="([^"]+)"', full_text)
    comm = comm_match.group(1) if comm_match else (cmd_args[0] if cmd_args else "unknown")
    # Return format: (comm_name, source_context, running_context)
    return (comm, scontext, running_context)


def _check_process_contexts_from_audit(start_time, end_time=None):
    """Check SELinux contexts of executed processes from audit logs.
    Groups lines by event ID to correlate EXECVE arguments with SYSCALL context.
    """
    contexts = []

    # Prepare ausearch command
    # Note: We search for both SYSCALL and EXECVE to ensure we get the full block
    cmd = [
        "ausearch",
        "--message",
        "SYSCALL,EXECVE",
        "--start",
        start_time.strftime("%m/%d/%Y"),
        start_time.strftime("%H:%M:%S"),
    ]
    if end_time:
        cmd.extend(["--end", end_time.strftime("%m/%d/%Y"), end_time.strftime("%H:%M:%S")])

    # Helper to process a block of lines
    def process_block(lines):
        if not lines:
            return
        parsed = _parse_execve_event_block(lines)
        if parsed:
            contexts.append(parsed)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
    if result.returncode == 0 and result.stdout:
        current_event = []
        for line in result.stdout.splitlines():
            if line.strip() == "----":
                process_block(current_event)
                current_event = []
            else:
                current_event.append(line)
        process_block(current_event)  # Process the last block
    return contexts


# Classes
class AuditLogEntry:
    def __init__(self, keys, values):
        self.fields = dict(zip(keys, values))

    def __getitem__(self, item):
        return self.fields[item]

    def __str__(self):
        return subprocess.run(
            ["ausearch", "-i", "-a", f"{self.serial}"], stdout=subprocess.PIPE, check=True
        ).stdout.decode()

    @property
    def serial(self):
        return self["event"]


class SELinuxAVCChecker:
    """Context manager for checking SELinux avc during a time period.
    This context manager automatically tracks start_time and end_time,
    removing the need for manual time tracking in tests.
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.avc_skiplist = []

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        return False

    def skip_avc_re(self, expression):
        expression = re.compile(expression)
        condition = lambda entry: re.search(expression, str(entry))  # noqa: E731
        self.avc_skiplist.append(condition)
        return condition

    def skip_avc_entry_by_fields(self, fields):
        condition = lambda entry: all(  # noqa: E731
            entry[key] == value for key, value in fields.items()
        )
        self.avc_skiplist.append(condition)
        return condition

    def skip_all_avcs(self):
        condition = lambda entry: True  # noqa: E731
        self.avc_skiplist.append(condition)
        return condition

    def get_avcs(self, skiplisted=True):
        lines = (
            subprocess.run(self.aureport_command, stdout=subprocess.PIPE)
            .stdout.decode()
            .splitlines()
        )
        assert lines.pop(0) == ""
        assert lines.pop(0) == "AVC Report"
        assert lines.pop(0) == "==============================================================="
        keys = lines.pop(0).split()
        assert lines.pop(0) == "==============================================================="
        if lines[0] == "<no events of interest were found>":
            return
        for line in lines:
            if not line:  # skip empty lines
                continue
            entry = AuditLogEntry(keys, line.split())
            if skiplisted and any(condition(entry) for condition in self.avc_skiplist):
                continue
            yield entry

    @property
    def start_aureport_time(self):
        return self.start_time.strftime("%m/%d/%Y"), self.start_time.strftime("%H:%M:%S")

    @property
    def end_aureport_time(self):
        return self.end_time.strftime("%m/%d/%Y"), self.end_time.strftime("%H:%M:%S")

    @property
    def aureport_command(self):
        cmd = [
            "aureport",
            "--avc",
            "--interpret",
            "--start",
            *self.start_aureport_time,
        ]
        if self.end_time:
            cmd += ["--end", *self.end_aureport_time]
        return cmd

    def get_denials(self, proc=None):
        # Get AVC denials that occurred during the context manager period.
        return list(self.get_avcs())

    def get_process_contexts(self):
        # Get process contexts from execve events during the context manager period.
        return _check_process_contexts_from_audit(self.start_time, self.end_time)
