from pyterraformer import HumanSerializer

def standard_string(string:str):
    return ' '.join(string.split())

def test_human_serialization():
    hs = HumanSerializer()
    example_string = '''resource "aws_s3_bucket" "b" {
      bucket = "my-tf-test-bucket"
    
      tags = {
        Name        = "My bucket"
        Environment = "Dev"
      }
    }
    
    resource "aws_s3_bucket" "b2" {
      bucket = "my-tf-test-bucket"
    
      tags = {
        Name        = "My bucket"
        Environment = "Dev"
      }
    }'''
    bucket = hs.parse_string(example_string)[0]

    bucket.tags["Environment"] = "Prod"
    bucket.bucket = 'my-updated-bucket'

    test_string =  '''resource "aws_s3_bucket" "b" {
      bucket = "my-updated-bucket"
    
      tags = {
        Name        = "My bucket"
        Environment = "Prod"
      }
    }'''

    updated = hs.render_object(bucket)

    assert standard_string(updated) == standard_string(test_string)