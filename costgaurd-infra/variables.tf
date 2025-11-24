variable "aws_region" {
  type    = string
  default = "us-east-1"
}


variable "ec2_key_name" {
  type = string
}

variable "ec2_ami_id" {
  type    = string
  default = "ami-0c02fb55956c7d316" # Amazon Linux 2 in us-east-1
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "s3_bucket_name" {
  type = string
}

