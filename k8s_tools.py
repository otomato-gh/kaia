import subprocess

def call_kubectl(command: str) -> str:
    """Call any kubectl command in the current cluster context"""
    if command == '':
        return subprocess.check_output(['kubectl', ''])
    if command.split()[0] != 'kubectl':
        command = 'kubectl ' + command
    return (subprocess.check_output(command.split()))

def call_shell(command: str) -> str:
    """Call generic shell command """
    return (subprocess.check_output(command.split()))