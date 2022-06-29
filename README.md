[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/wayfair-incubator/pyterraformer/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pyterraformer.svg)](https://pypi.org/project/pyterraformer/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyterraformer.svg)](https://pypi.python.org/pypi/pyterraformer)
[![Downloads](https://img.shields.io/badge/dynamic/json.svg?label=downloads&url=https%3A%2F%2Fpypistats.org%2Fapi%2Fpackages%2Fpyterraformer%2Frecent&query=data.last_month&colorB=brightgreen&suffix=%2FMonth)](https://pypistats.org/packages/pyterraformer)

# OSPO Project Template

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.0-4baaaa.svg)](CODE_OF_CONDUCT.md)

## About The Project

Pyterraformer is a library for reading, modifying, and writing *human readable terraform code*. This is in contrast to
libraries such as the excellent [pyhcl2](https://github.com/amplify-education/python-hcl2), which don't support writing
back in the human format. It is similar to [terraform-cdk](https://www.terraform.io/cdktf) in that it also enables
directly executing terraform from python as well, but is different in that it can produce human readable code to check
in. This opens up a range of options for creative developers.

Pyterraformer can be used for any of the following:

- bulk generation of human readable terraform code
- large scale refactoring
- process automation, since as CI
- accessing the power of Terraform directly from python
- introspecting a terraform repo to collect information
- and more!

## Parsing and Modifying

Specifically, this library would enable reading this string

```terraform
resource "aws_s3_bucket" "b" {
  bucket = "my-tf-test-bucket"

  tags = {
    Name = "My bucket"
    Environment = "Dev"
  }
}
```

into python, directly modifying the tags, and writing it back.

Let's take a look.

```python
from pyterraformer import HumanSerializer

hs = HumanSerializer(terraform='/path/to/my/terraform/binary')

example_string = '''resource "aws_s3_bucket" "b" {
  bucket = "my-tf-test-bucket"

  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}'''

# parse a string into a list of terraform objects
namespace = hs.parse_string(example_string)

# get the bucket from that list
bucket = namespace.objects[0]

# modify the bucket
bucket.tags["Environment"] = "Prod"
bucket.bucket = 'my-updated-bucket'

# and write the modified namespace back
# formatting requires a valid terraform binary to be provided
updated = hs.render_object(bucket, format=True)

assert updated == '''resource "aws_s3_bucket" "b" {
  bucket = "my-updated-bucket"

  tags = {
    Name        = "My bucket"
    Environment = "Prod"
  }
}
'''

```

## Applying

If you just want to directly create/modify resources, you can do that too.

For example, creating or modifying GCS bucket with a local state store is as simple as the below.

```python
import os

from pyterraformer import Terraform, TerraformWorkspace, HumanSerializer, LocalBackend
from pyterraformer.core.generics import BlockList
from pyterraformer.core.resources import ResourceObject


class GoogleStorageBucket(ResourceObject):
    """Let's define a google storge bucket resource.
    To get provider resources defined for you, check out the provider packages."""
    _type = 'google_storage_bucket'


if __name__ == "__main__":
    tf = Terraform(terraform_exec_path=r'/path/to/my/terraform/binary',
                   backend=LocalBackend(path=os.getcwd()))
    workspace = TerraformWorkspace(terraform=tf, path=os.getcwd(), serializer=HumanSerializer(terraform=tf))

    namespace = workspace.get_file_safe('resource.tf')

    namespace.add_object(GoogleStorageBucket(
        id='my-new-bucket',
        name="my-new-bucket",
        location="US-EAST1",
        project="my-project",
        force_destroy=True,
        uniform_bucket_level_access=True,
        website=BlockList([{
            'not_found_page': "404.html"
        }]),
        cors=BlockList([{
            'origin': [
                "https://readthedocs.org"],
            'method': [
                "GET",
                "HEAD",
                "PUT",
                "POST",
                "DELETE"],
            'response_header': [
                "*"],
            'max_age_seconds': 3601
        }])
    ))

    workspace.save()

    application_output = workspace.apply()
```

## Next Steps

Read the [documentation](https://pyterraformer.readthedocs.io/en/latest/) to discover more, including how to work with
directories, files, apply terraform directly, and get IDE auto-completion for your favorite providers.

## Project Maturity
`pyterraformer` is under active development; we’re still working out key workflows and best practices. While it has
been used extensively in internal projects, the open-source version contains significant rewrites for improved flexibility. 
We’re iterating fast and are likely to introduce breaking changes to existing APIs to improve the developer experience.
Feedback is appreciated.

### Installation

`pyterraformer` is [hosted on PyPI](https://pypi.org/project/pyterraformer/), and is installable
with [pip](https://pip.pypa.io/en/stable/):

```sh
pip install pyterraformer
```

Typed classes for IDE autocomplete and validation [if available] can be installed under the package name
pytf-[provider-owner]-[provider-name]

```sh
pip install pytf-hashicorp-aws

```

And then imported in the following way

```python
from pyterraformer.providers.hashicorp.aws import aws_s3_bucket

```

## Documentation

Primary documentation is on [Read the Docs](https://pyterraformer.readthedocs.io/en/latest/)

## Roadmap

See the [open issues](https://github.com/org_name/repo_name/issues) for a list of proposed features (and known issues).

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any
contributions you make are **greatly appreciated**. For detailed contributing guidelines, please
see [CONTRIBUTING.md](CONTRIBUTING.md)

## License

Distributed under the `MIT License` License. See `LICENSE` for more information.

## Contact

Project Link: [https://github.com/org_name/repo_name](https://github.com/org_name/repo_name)

## Acknowledgements

This template adapted from
[https://github.com/othneildrew/Best-README-Template](https://github.com/othneildrew/Best-README-Template)
