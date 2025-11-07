# Launch Template
resource "aws_launch_template" "this" {
  name_prefix   = "${var.project}-lt"
  image_id      = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name

  network_interfaces {
    security_groups = [var.ec2_sg_id]
    associate_public_ip_address = false
  }

  user_data = base64encode(<<-EOT
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "Hello from ${var.project} App Server" > /var/www/html/index.html
              EOT
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project}-ec2"
    }
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "this" {
  desired_capacity     = var.desired_capacity
  max_size             = var.max_size
  min_size             = var.min_size
  vpc_zone_identifier  = var.private_subnets
  health_check_type    = "EC2"

  launch_template {
    id      = aws_launch_template.this.id
    version = "$Latest"
  }

  target_group_arns = [var.target_group_arn]

  tag {
    key                 = "Name"
    value               = "${var.project}-asg"
    propagate_at_launch = true
  }
}

# Scaling Policies (optional)
resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.project}-scale-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.this.name
}

resource "aws_autoscaling_policy" "scale_down" {
  name                   = "${var.project}-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.this.name
}

# Defines a Launch Template for EC2 with:

# Security group (only allows traffic from ALB SG).

# Apache installed + simple webpage (Hello from securon App Server).

# Defines an Auto Scaling Group across private subnets.

# Attaches EC2 instances to the ALB Target Group automatically.

# Includes scale-up / scale-down policies (basic, optional).