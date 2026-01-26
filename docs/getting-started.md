# Getting Started

## Installation

To install `pyterraformer`, simply run this simple command in your terminal of choice:

```bash
python -m pip install pyterraformer
```

## Requirements

- Python 3.10 or higher
- (Optional) A terraform binary for formatting output

## Introduction

`pyterraformer` enables reading, modifying, and writing human-readable terraform code directly from Python.

### Basic Usage

```python
from pyterraformer import HumanSerializer

# Create a serializer instance
hs = HumanSerializer(terraform='/path/to/terraform/binary')

# Parse terraform code from a string
terraform_code = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
}
'''
namespace = hs.parse_string(terraform_code)

# Access and modify resources
bucket = namespace[0]
bucket.bucket = "my-new-bucket"

# Render back to terraform code
output = hs.render_object(bucket, format=True)
```

### Working with Files

```python
from pyterraformer import TerraformWorkspace, HumanSerializer, Terraform, LocalBackend
import os

# Set up the terraform workspace
tf = Terraform(
    terraform_exec_path='/path/to/terraform',
    backend=LocalBackend(path=os.getcwd())
)
workspace = TerraformWorkspace(
    terraform=tf,
    path=os.getcwd(),
    serializer=HumanSerializer(terraform=tf)
)

# Load a terraform file
namespace = workspace.get_file_safe('main.tf')

# Make modifications and save
workspace.save()
```

## What's Next?

- Read the [Development Guide](development-guide.md) to learn how to contribute
- Check out the [Changelog](changelog.md) for recent updates

[docs-main]: index.md
