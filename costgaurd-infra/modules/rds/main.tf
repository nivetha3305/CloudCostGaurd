resource "aws_db_subnet_group" "this" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = var.db_subnets

  tags = {
    Name = "${var.project}-db-subnet-group"
  }
}

resource "aws_db_instance" "this" {
  identifier              = "${var.project}-db"
  engine                  = var.db_engine
  engine_version          = var.db_engine_version
  instance_class          = var.db_instance_class
  allocated_storage       = var.allocated_storage
  max_allocated_storage   = var.max_allocated_storage
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.this.name
  vpc_security_group_ids  = [var.rds_sg_id]
  multi_az                = false
  skip_final_snapshot     = true
  publicly_accessible     = false
  deletion_protection     = false

  backup_retention_period = 7
  storage_encrypted       = true

  tags = {
    Name = "${var.project}-rds"
  }
}

# Creates an RDS subnet group using private subnets.

# Deploys an RDS instance:

# Defaults: MySQL 8.0, db.t3.micro, 20GB (auto grows to 100GB).

# Private-only (not publicly accessible).

# Encrypted storage + automated backups.

# Exposes DB endpoint (to connect from EC2).

# Master credentials passed via variables (you can later move these to SSM Parameter Store for security).