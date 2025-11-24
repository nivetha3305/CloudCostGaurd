terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region

  # Dummy values so Terraform never tries AWS authentication
  access_key                  = "FAKE"
  secret_key                  = "FAKE"

  # Disable all validation so AWS is NOT contacted
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}
