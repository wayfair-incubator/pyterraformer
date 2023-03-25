resource "aws_s3_bucket" "b" {
  test = false
  # maintain position
  bucket = "my-tf-test-bucket"
  # this is a helpful comment
  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}