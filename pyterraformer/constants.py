from os import environ, listdir
from os.path import isdir

TERRAFORM_EXEC = environ.get('TERRAFORM_EXEC', None)

TERRAFORM_EXEC_VERSIONS = {}

if TERRAFORM_EXEC and isdir(TERRAFORM_EXEC):
    children = listdir(TERRAFORM_EXEC)
    for child in children:
        print(child)


print(TERRAFORM_EXEC)