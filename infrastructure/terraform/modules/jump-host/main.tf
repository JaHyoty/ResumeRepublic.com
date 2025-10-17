# Jump host for database access via SSM Session Manager
resource "aws_instance" "jump_host" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.database_subnet_id
  vpc_security_group_ids = [aws_security_group.jump_host.id]
  iam_instance_profile   = aws_iam_instance_profile.jump_host.name

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    db_host = var.database_host
    db_port = var.database_port
  }))

  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-${var.environment}-jump-host"
    AccessRole  = "jump-host"
    Description = "Jump host for database access via SSM Session Manager"
  })
}

# Security group for jump host
resource "aws_security_group" "jump_host" {
  name_prefix = "${var.project_name}-${var.environment}-jump-host-"
  vpc_id      = var.vpc_id

  # Allow outbound HTTPS for SSM Session Manager
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for SSM Session Manager"
  }

  # Allow outbound to database
  egress {
    from_port       = var.database_port
    to_port         = var.database_port
    protocol        = "tcp"
    security_groups = [var.database_security_group_id]
    description     = "Database access"
  }

  # Allow outbound HTTP for package updates
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP for package updates"
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-jump-host-sg"
  })
}

# IAM role for jump host
resource "aws_iam_role" "jump_host" {
  name = "${var.project_name}-${var.environment}-jump-host-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Attach SSM managed instance core policy
resource "aws_iam_role_policy_attachment" "jump_host_ssm" {
  role       = aws_iam_role.jump_host.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM instance profile
resource "aws_iam_instance_profile" "jump_host" {
  name = "${var.project_name}-${var.environment}-jump-host-profile"
  role = aws_iam_role.jump_host.name

  tags = var.common_tags
}

# Data source for latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Outputs
output "jump_host_instance_id" {
  description = "Instance ID of the jump host"
  value       = aws_instance.jump_host.id
}

output "jump_host_security_group_id" {
  description = "Security group ID of the jump host"
  value       = aws_security_group.jump_host.id
}
