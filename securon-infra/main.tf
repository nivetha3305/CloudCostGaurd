module "vpc" {
  source = "./modules/vpc"
  vpc_cidr = "10.0.0.0/16"
}

module "security_groups" {
  source     = "./modules/security_groups"
  vpc_id     = module.vpc.vpc_id
}

module "alb" {
  source       = "./modules/alb"
  vpc_id       = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets
  alb_sg_id    = module.security_groups.alb_sg_id
  
}

module "ec2" {
  source           = "./modules/ec2"
  
  private_subnets  = module.vpc.private_subnets   # ✅ Added
  ec2_sg_id        = module.security_groups.ec2_sg_id
  key_name         = var.ec2_key_name
  ami_id           = var.ec2_ami_id              # ✅ Added
  target_group_arn = module.alb.target_group_arn # ✅ Added
}


module "rds" {
  source          = "./modules/rds"
  db_subnets      = module.vpc.private_subnets
  rds_sg_id       = module.security_groups.rds_sg_id
  db_username     = var.db_username
  db_password     = var.db_password
}

module "s3" {
  source   = "./modules/s3"
  bucket_name = var.s3_bucket_name
}
