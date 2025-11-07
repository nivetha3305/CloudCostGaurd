# pricing/others_pricing.py

def get_cost(resource):
    res_type = resource.get("type")

    # Define resource-type specific logic
    if res_type in [
        "aws_security_group", "aws_security_group_rule", "aws_subnet",
        "aws_vpc", "aws_route_table", "aws_route_table_association",
        "aws_lb_target_group", "aws_s3_bucket_public_access_block",
        "aws_s3_bucket_versioning", "aws_s3_bucket_server_side_encryption_configuration",
        "aws_db_subnet_group"
    ]:
        return {"monthly_cost": 0.0, "note": "(Free resource)"}

    elif res_type == "aws_internet_gateway":
        # Example: small outbound traffic estimate
        estimated_cost = 0.09 * 10  # 10 GB × $0.09
        return {"monthly_cost": round(estimated_cost, 2), "note": "10GB data transfer"}

    elif res_type == "aws_autoscaling_group":
        # Example: 2 small instances x 720 hours
        hourly_rate = 0.0104
        cost = 2 * hourly_rate * 720
        return {"monthly_cost": round(cost, 2), "note": "Auto-scaling ~2× t3.micro"}

    else:
        return {"monthly_cost": 0.0, "note": "(Pricing not implemented)"}
