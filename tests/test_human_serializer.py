from pyterraformer import HumanSerializer


def standard_string(string: str):
    return " ".join(string.split())


def test_human_serialization():
    hs = HumanSerializer()
    example_string = """resource "aws_s3_bucket" "b" {
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
    }"""
    bucket = hs.parse_string(example_string)[0]

    bucket.tags["Environment"] = "Prod"
    bucket.bucket = "my-updated-bucket"

    test_string = """resource "aws_s3_bucket" "b" {
      bucket = "my-updated-bucket"
    
      tags = {
        Name        = "My bucket"
        Environment = "Prod"
      }
    }"""

    updated = hs.render_object(bucket)

    assert standard_string(updated) == standard_string(test_string)


def test_block_parsing(human_serializer):

    split = """terraform {
  backend "local" {

  }
  required_providers {
    test = {
      source = "hashicorp/google"
      version = "4.27.0"
    }
  }
  required_providers {
    build = {
      source  = "hashicorp/google"
      version = "4.27.0"
    }
  }
}

"""
    parsed_split = human_serializer.parse_string(split)[0]
    assert len(parsed_split.required_providers) == 2

    joined = """terraform {
  backend "local" {

  }
  required_providers {
    test = {
      source = "hashicorp/google"
      version = "4.27.0"
    }
    build = {
      source  = "hashicorp/google"
      version = "4.27.0"
    }
  }
}

"""
    parsed_joined = human_serializer.parse_string(joined)[0]

    assert len(parsed_joined.required_providers) == 2


def test_block_parsing_variants(human_serializer):

    split = """terraform {
  backend "local" {

  }
  required_providers {
    test = {
      source = "hashicorp/google"
      version = "4.27.0"
    }
  }
  required_providers {
    build = {
      source  = "hashicorp/google"
      version = "4.27.0"
    }
  }
}

"""

    joined = """terraform {
  backend "local" {

  }
  required_providers {
    test = {
      source = "hashicorp/google"
      version = "4.27.0"
    }
    build = {
      source  = "hashicorp/google"
      version = "4.27.0"
    }
  }
}

"""
    parsed_split = human_serializer.parse_string(split)[0]
    parsed_joined = human_serializer.parse_string(joined)[0]

    assert parsed_split.required_providers == parsed_joined.required_providers


def test_comments(human_serializer):

    split = """resource "google_container_cluster" "primary" {
  name     = "my-gke-cluster"
  location = "us-central1"

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
}
"""
    parsed_split = human_serializer.parse_string(split)[0]

    rendered = human_serializer.render_object(parsed_split)
    print(rendered)
    assert (
        """# We can't create a cluster with no node pool defined, but we want to only use
# separately managed node pools. So we create the smallest possible default
# node pool and immediately delete it."""
        in rendered
    )
