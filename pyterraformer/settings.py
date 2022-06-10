def get_default_terraform_location()->Optional[str]:
    '''Attempt to discover default terraform location'''
    from platform import system
    from subprocess import CalledProcessError, run
    if system() == 'Windows':
        cmd = ['where', 'terraform']
    else:
        cmd = ['which', 'terraform']

    try:
        output = run(cmd, check=True, capture_output=True, encoding="utf-8")
        if output.stdout:
            output = output.stdout.strip()
            return output
    except CalledProcessError:
        return None