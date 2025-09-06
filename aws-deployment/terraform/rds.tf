# RDS PostgreSQL Database
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-db-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.app_name}-db"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true
  
  db_name  = "careerpathpro"
  username = "careeruser"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = var.environment != "production"
  deletion_protection = var.environment == "production"
  
  tags = {
    Name = "${var.app_name}-db"
  }
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "db_port" {
  value = aws_db_instance.main.port
}
