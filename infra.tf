provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "CryptoVPC"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 5
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone = element(["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d", "us-east-1e"], count.index)
  map_public_ip_on_launch = true
  tags = {
    Name = "PublicSubnet-${count.index}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 5
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 5)
  availability_zone = element(["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d", "us-east-1e"], count.index)
  tags = {
    Name = "PrivateSubnet-${count.index}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "MainIGW"
  }
}

# NAT Gateways and EIPs for each public subnet
resource "aws_eip" "nat" {
  count = length(aws_subnet.public)
  domain = "vpc"
}

resource "aws_nat_gateway" "nat" {
  count      = length(aws_subnet.public)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}

# Route Tables and Associations for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Tables and Associations for Private Subnets
resource "aws_route_table" "private" {
  count   = length(aws_subnet.public)
  vpc_id  = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat[count.index].id
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = element(aws_route_table.private.*.id, count.index)
}
# ECS Cluster
resource "aws_ecs_cluster" "cluster" {
  name = "full-service-cluster"
}

# EFS File System
resource "aws_efs_file_system" "full_service_fs" {
  creation_token = "full-service-fs"
  tags = {
    Name = "FullServiceFileSystem"
  }
}

# EFS Mount Target in Private Subnets
resource "aws_efs_mount_target" "efs_mt" {
  count           = length(aws_subnet.private)
  file_system_id  = aws_efs_file_system.full_service_fs.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs_sg.id]
}

# Security Group for EFS
resource "aws_security_group" "efs_sg" {
  name        = "efs-sg"
  description = "Allow NFS for EFS"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Role for ECS Execution
resource "aws_iam_role" "ecs_execution_role" {
  name = "ecs_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      },
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name = "/ecs/full-service"
}

resource "aws_cloudwatch_log_group" "ecs_web_log_group" {
  name = "/ecs/web-service"
}


resource "aws_efs_access_point" "access_point" {
  file_system_id = aws_efs_file_system.full_service_fs.id
  posix_user {
    uid = 1000  # UID of the user in your container
    gid = 1000  # GID of the user in your container
  }
  root_directory {
    path = "/data"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }
}

resource "aws_iam_role" "ecs_task_role" {
  name = "ecs_task_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      },
    }]
  })
}

resource "aws_iam_role_policy" "efs_access" {
  name   = "efs_access"
  role   = aws_iam_role.ecs_task_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = [
        "elasticfilesystem:ClientMount",
        "elasticfilesystem:ClientWrite",
        "elasticfilesystem:DescribeFileSystems"
      ],
      Effect   = "Allow",
      Resource = "*"
    }]
  })
}

# ECS Task Definition with Log Configuration
resource "aws_ecs_task_definition" "full_service" {
  family                   = "full-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "2048"
  memory                   = "13312"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  volume {
    name = "full-service-data"
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.full_service_fs.id
      root_directory = "/"
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.access_point.id
        iam             = "ENABLED"
      }
    }
  }
  task_role_arn = aws_iam_role.ecs_task_role.arn
  container_definitions = jsonencode([{
    name  = "full-service",
    image = "mobilecoin/full-service:v2.9.2-mainnet",
    portMappings = [{
      containerPort = 9090,
      hostPort      = 9090
    }],
    mountPoints = [{
      sourceVolume  = "full-service-data",
      containerPath = "/data",
      readOnly      = false
    }],
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:9090/wallet/v2 || exit 1"],
      interval    = 30,
      timeout     = 10,
      retries     = 10,
      startPeriod = 10
    },
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.ecs_log_group.name
        awslogs-region        = "us-east-1"
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

# Application Load Balancer (Internal)
resource "aws_lb" "app_lb" {
  name               = "full-service-lb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = aws_subnet.private[*].id
}

# ALB Target Group
resource "aws_lb_target_group" "tg" {
  name     = "full-service-tg"
  port     = 9090
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  target_type = "ip"
  health_check {
    enabled             = true
    interval            = 60
    path                = "/wallet/v2"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    matcher             = "200"
  }
}

# ALB Listener
resource "aws_lb_listener" "listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}

# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  description = "Security group for internal ALB"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]  # Restrict to VPC CIDR
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main.cidr_block]  # Restrict to VPC CIDR
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks_sg" {
  name        = "ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port = 9090
    to_port = 9090
    protocol = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_web_sg" {
  name        = "ecs-web-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port = 8000
    to_port = 8000
    protocol = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# ECS Service
resource "aws_ecs_task_definition" "web" {
  family                   = "web-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{
    name  = "web",
    image = "jayzalowitz/secretpoet.1.8",  # Replace with your Docker image
    # command = ["/app/remote-up.sh"],  # Specify the path to your script
    portMappings = [{
      containerPort = 8000,
      hostPort      = 8000
    }],
    environment = [
      { name = "DATABASE_URL", value = "postgres://${var.DB_USER}:${var.DB_PASS}@${aws_db_instance.db.endpoint}/${var.DB_NAME}" },
      { name = "FULL_SERVICE_URL", value = "http://${aws_lb.app_lb.dns_name}:80/wallet/v2" },
      { name = "DJANGO_SUPERUSER_USERNAME", value = var.DJANGO_SUPERUSER_USERNAME },
      { name = "DJANGO_SUPERUSER_EMAIL", value = var.DJANGO_SUPERUSER_EMAIL },
      { name = "DJANGO_SUPERUSER_PASSWORD", value = var.DJANGO_SUPERUSER_PASSWORD }
    ],
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/healthcheck/ || exit 1"],
      interval    = 60,
      timeout     = 10,
      retries     = 3,
      startPeriod = 10
    },
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.ecs_web_log_group.name
        awslogs-region        = "us-east-1"
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

## ECS Service LB
resource "aws_ecs_service" "full_service" {
  name            = "full-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.full_service.arn
  launch_type     = "FARGATE"
  network_configuration {
    subnets = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_tasks_sg.id]
  }
  desired_count = 1
  force_new_deployment = true
  load_balancer {
    target_group_arn = aws_lb_target_group.tg.arn
    container_name   = "full-service"
    container_port   = 9090
  }
}

# Web service only
resource "aws_lb" "web_alb" {
  name               = "web-service-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.web_alb_sg.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_security_group" "web_alb_sg" {
  name        = "web-alb-sg"
  description = "Security group for web ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main.cidr_block]  # Restrict to VPC CIDR
  }
}

resource "aws_lb_target_group" "web_tg" {
  name     = "web-service-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    interval            = 60
    path                = "/healthcheck/"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    matcher             = "200"
  }
}

resource "aws_lb_listener" "web_listener" {
  load_balancer_arn = aws_lb.web_alb.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_tg.arn
  }
}

resource "aws_ecs_service" "web_service" {
  name            = "web-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.web.arn
  launch_type     = "FARGATE"
  desired_count   = 2
  force_new_deployment = true

  network_configuration {
    subnets = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_web_sg.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web_tg.arn
    container_name   = "web"
    container_port   = 8000
  }
}

# end web service

# RDS ONLY
resource "aws_db_instance" "db" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.t3.micro"
  identifier           = var.DB_NAME
  db_name              = var.DB_NAME
  username             = var.DB_USER
  password             = var.DB_PASS
  parameter_group_name = "default.postgres15"
  db_subnet_group_name = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot  = true
}

resource "aws_db_subnet_group" "db_subnet_group" {
  name       = "my-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "db_sg" {
  name        = "db-sg"
  description = "Database security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
}
# End rds



variable "DB_NAME" {
  default = "yourdbname"
}

variable "DB_USER" {
  default = "youruser"
}

variable "DB_PASS" {
  default = "yourpassword"
}

variable "DJANGO_SUPERUSER_USERNAME" {
  default = "myusername"
}

variable "DJANGO_SUPERUSER_EMAIL" {
  default = "myemail@example.com"
}

variable "DJANGO_SUPERUSER_PASSWORD" {
  default = "mypassword"
}

output "external_service_endpoint" {
  value = aws_lb.web_alb.dns_name
}

output "internal_service_endpoint" {
  value = aws_lb.app_lb.dns_name
}