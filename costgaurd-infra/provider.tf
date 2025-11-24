=terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Fake static credentials so Terraform does NOT try
  # to load local AWS profiles or AWS SSO
  access_key = "FAKE_ACCESS_KEY"
  secret_key = "FAKE_SECRET_KEY"
}
