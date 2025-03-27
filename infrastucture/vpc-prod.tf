# VPC for prod environment
resource "aws_vpc" "container_vpc_prod" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "container_vpc_prod" }
}

# Public Subnets for prod environment
resource "aws_subnet" "container_public_az1_prod" {
  vpc_id                  = aws_vpc.container_vpc_prod.id
  cidr_block              = "10.1.1.0/24"
  availability_zone       = "ap-northeast-1a"
  map_public_ip_on_launch = true
  tags                    = { Name = "container_public_az1_prod" }
}

resource "aws_subnet" "container_public_az2_prod" {
  vpc_id                  = aws_vpc.container_vpc_prod.id
  cidr_block              = "10.1.2.0/24"
  availability_zone       = "ap-northeast-1c"
  map_public_ip_on_launch = true
  tags                    = { Name = "container_public_az2_prod" }
}

# Private Subnets for prod environment
resource "aws_subnet" "container_private_az1_prod" {
  vpc_id            = aws_vpc.container_vpc_prod.id
  cidr_block        = "10.1.3.0/24"
  availability_zone = "ap-northeast-1a"
  tags              = { Name = "container_private_az1_prod" }
}

resource "aws_subnet" "container_private_az2_prod" {
  vpc_id            = aws_vpc.container_vpc_prod.id
  cidr_block        = "10.1.4.0/24"
  availability_zone = "ap-northeast-1c"
  tags              = { Name = "container_private_az2_prod" }
}

# DB Subnets for prod environment
resource "aws_subnet" "container_db_az1_prod" {
  vpc_id            = aws_vpc.container_vpc_prod.id
  cidr_block        = "10.1.5.0/24"
  availability_zone = "ap-northeast-1a"
  tags              = { Name = "container_db_az1_prod" }
}

resource "aws_subnet" "container_db_az2_prod" {
  vpc_id            = aws_vpc.container_vpc_prod.id
  cidr_block        = "10.1.6.0/24"
  availability_zone = "ap-northeast-1c"
  tags              = { Name = "container_db_az2_prod" }
}

# Internet Gateway for prod environment
resource "aws_internet_gateway" "container_IGW_prod" {
  vpc_id = aws_vpc.container_vpc_prod.id
  tags   = { Name = "container_IGW_prod" }
}

# Public Route Table for prod environment
resource "aws_route_table" "container_public_rtb_prod" {
  vpc_id = aws_vpc.container_vpc_prod.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.container_IGW_prod.id
  }
  tags = { Name = "container_public_rtb_prod" }
}

# Route Table Associations for public subnets
resource "aws_route_table_association" "public_az1_prod" {
  subnet_id      = aws_subnet.container_public_az1_prod.id
  route_table_id = aws_route_table.container_public_rtb_prod.id
}

resource "aws_route_table_association" "public_az2_prod" {
  subnet_id      = aws_subnet.container_public_az2_prod.id
  route_table_id = aws_route_table.container_public_rtb_prod.id
}

# Elastic IP for NAT Gateway
resource "aws_eip" "container_eip_prod" {}

# NAT Gateway for prod environment
resource "aws_nat_gateway" "container_NGW_prod" {
  subnet_id     = aws_subnet.container_public_az1_prod.id
  allocation_id = aws_eip.container_eip_prod.id
  tags          = { Name = "container_NGW_prod" }
}

# Private Route Table for prod environment
resource "aws_route_table" "container_private_rtb_prod" {
  vpc_id = aws_vpc.container_vpc_prod.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.container_NGW_prod.id
  }
  tags = { Name = "container_private_rtb_prod" }
}

# Route Table Associations for private subnets
resource "aws_route_table_association" "private_az1_prod" {
  subnet_id      = aws_subnet.container_private_az1_prod.id
  route_table_id = aws_route_table.container_private_rtb_prod.id
}

resource "aws_route_table_association" "private_az2_prod" {
  subnet_id      = aws_subnet.container_private_az2_prod.id
  route_table_id = aws_route_table.container_private_rtb_prod.id
}

# Security Group for public instances (allow HTTP, HTTPS)
resource "aws_security_group" "container_public_sg_prod" {
  vpc_id      = aws_vpc.container_vpc_prod.id
  name        = "container_public_sg_prod"
  description = "allow http, https"
  tags        = { Name = "container_public_sg_prod" }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 8080
    to_port     = 8080
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
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security Group for private instances (allow traffic from ELB Subnets)
resource "aws_security_group" "container_private_sg_prod" {
  vpc_id      = aws_vpc.container_vpc_prod.id
  name        = "container_private_sg_prod"
  description = "allow traffic from ELB Subnets"
  tags        = { Name = "container_private_sg_prod" }
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.container_public_sg_prod.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
