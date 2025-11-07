variable "project" {
  description = "Project name prefix"
  type        = string
  default     = "securon"
}

variable "vpc_id" {
  description = "VPC ID where SGs will be created"
  type        = string
}

variable "db_port" {
  description = "Database port (3306 for MySQL, 5432 for PostgreSQL)"
  type        = number
  default     = 3306
}
