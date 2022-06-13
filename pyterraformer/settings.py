from typing import Optional


def get_default_terraform_location() -> Optional[str]:
    """Attempt to discover default terraform location"""
    from platform import system
    from subprocess import CalledProcessError, run

    if system() == "Windows":
        cmd = ["where", "terraform"]
    else:
        cmd = ["which", "terraform"]

    try:
        output = run(cmd, check=True, capture_output=True, encoding="utf-8")
        if output.stdout:
            # where may return multiple lines
            output = output.stdout.split("\n")[0].strip()
            return output
    except CalledProcessError:
        return None
