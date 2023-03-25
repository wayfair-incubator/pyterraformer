from pyterraformer.exceptions import TerraformExecutionError
import pytest


def test_readme():
    from pyterraformer import HumanSerializer

    hs = HumanSerializer(terraform="/path/to/my/terraform/binary/does/not/exist")

    example_string: str = """resource "aws_s3_bucket" "b" {
      bucket = "my-tf-test-bucket"
      
      tags = {
    Name        = "My bucket"
        Environment = "Dev"
      }
    }"""

    # parse a string into a list of terraform objects
    namespace = hs.parse_string(example_string)

    # get the bucket from that list
    bucket = namespace[0]

    # modify the bucket
    bucket.tags["Environment"] = "Prod"
    bucket.bucket = "my-updated-bucket"

    # and write the modified namespace back
    # formatting requires a valid terraform binary to be provided
    with pytest.raises(TerraformExecutionError):
        updated = hs.render_object(bucket, format=True)
