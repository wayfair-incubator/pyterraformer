from os import environ


def get_default_terraform_location() -> str | None:
    """Attempt to discover default terraform location"""
    declared_path = environ.get("TERRAFORM_EXEC", None)
    if declared_path:
        return declared_path
    from platform import system
    from subprocess import CalledProcessError, run

    cmd = ["where", "terraform"] if system() == "Windows" else ["which", "terraform"]

    try:
        output = run(cmd, check=True, capture_output=True, encoding="utf-8")  # noqa: S603
        if output.stdout:
            # where may return multiple lines
            output_str = output.stdout.split("\n")[0].strip()
            return output_str
        return None
    except CalledProcessError:
        return None
