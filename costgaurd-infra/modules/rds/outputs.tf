# Outputs
output "db_endpoint" {
  value = aws_db_instance.this.endpoint
}

output "db_username" {
  value     = aws_db_instance.this.username
  sensitive = true
}
