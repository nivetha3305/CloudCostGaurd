variable "project" {
  description = "Project name prefix"
  type        = string
  default     = "securon"
}

variable "db_subnets" {
  description = "List of private subnets for DB"
  type        = list(string)
}

variable "rds_sg_id" {
  description = "Security Group ID for RDS"
  type        = string
}

variable "db_engine" {
  description = "Database engine (mysql or postgres)"
  type        = string
  default     = "mysql"
}

variable "db_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "8.0"
}

variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Initial storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Max autoscaling storage in GB"
  type        = number
  default     = 100
}

variable "db_username" {
  description = "Master DB username"
  type        = string
}

variable "db_password" {
  description = "Master DB password"
  type        = string
  sensitive   = true
}
