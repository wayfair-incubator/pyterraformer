# Pyterraformer - 0.1.0

[![CI pipeline status](https://github.com/wayfair-incubator/pyterraformer/workflows/CI/badge.svg?branch=main)][ci]
[![PyPI](https://img.shields.io/pypi/v/pyterraformer)](https://pypi.org/project/pyterraformer/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyterraformer)](https://pypi.org/project/pyterraformer/)

## About

Pyterraformer is a library for reading, modifying, and writing *human readable terraform code*. This is in contrast to
libraries such as the excellent [pyhcl2](https://github.com/amplify-education/python-hcl2), which don't support writing
back in the human format.

## Example

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
bucket = namespace[0]

# modify the bucket
bucket.tags["Environment"] = "Prod"
bucket.bucket = 'my-updated-bucket'

# and write the modified namespace back
updated = hs.render_object(bucket, format=True)
```

## Where to Start?

To learn the basics of how to start using `pyterraformer`, read the [Getting Started][getting_started] page.

## Detailed Documentation

To learn more about the various ways `pyterraformer` can be used, read the [Development Guide][development_guide] page.

[ci]: https://github.com/wayfair-incubator/pyterraformer/actions
[getting_started]: getting-started.md
[development_guide]: development-guide.md
