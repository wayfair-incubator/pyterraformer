# type: ignore
import ast
import re

import setuptools

_version_re = re.compile(r"__version__\s+=\s+(.*)")
with open("pyterraformer/__init__.py", "rb") as f:
    _match = _version_re.search(f.read().decode("utf-8"))
    if _match is None:
        print("No version found")
        raise SystemExit(1)
    version = str(ast.literal_eval(_match.group(1)))


with open("requirements.txt", "r") as f:
    install_requires = [line.strip().replace("==", ">=") for line in f.readlines()]

setuptools.setup(
    name="pyterraformer",
    version=version,
    url="",
    author="",
    author_email="pyterraformer@gmail.com",
    description="Enjoyable terraform manipulation from python.",
    long_description=open("README.md").read(),
    long_description_content_type='text/markdown',
    # package_dir={'':'pyterraformer'},
    packages=setuptools.find_packages(exclude=["dist", "build", "*.tests", "*.tests.*", "tests.*", "tests", "docs", ".github", "", "examples"]),
    package_data={
        "": ["*.tf", "*.jinja", "py.typed"],
    },
    install_requires=install_requires,
    scripts = ['scripts/create_provider_stubs.py'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
