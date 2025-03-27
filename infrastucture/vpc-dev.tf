# VPC for dev environment
resource "aws_vpc" "container_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "container_vpc" }
}

# Public Subnets for dev environment
resource "aws_subnet" "container_public_az1" {
  vpc_id                  = aws_vpc.container_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-northeast-1a"
  map_public_ip_on_launch = true
  tags                    = { Name = "container_public_az1" }
}

resource "aws_subnet" "container_public_az2" {
  vpc_id                  = aws_vpc.container_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "ap-northeast-1c"
  map_public_ip_on_launch = true
  tags                    = { Name = "container_public_az2" }
}

# Private Subnets for dev environment
resource "aws_subnet" "container_private_az1" {
  vpc_id            = aws_vpc.container_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "ap-northeast-1a"
  tags              = { Name = "container_private_az1" }
}

resource "aws_subnet" "container_private_az2" {
  vpc_id            = aws_vpc.container_vpc.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "ap-northeast-1c"
  tags              = { Name = "container_private_az2" }
}

# DB Subnets for dev environment
resource "aws_subnet" "container_db_az1" {
  vpc_id            = aws_vpc.container_vpc.id
  cidr_block        = "10.0.5.0/24"
  availability_zone = "ap-northeast-1a"
  tags              = { Name = "container_db_az1" }
}

resource "aws_subnet" "container_db_az2" {
  vpc_id            = aws_vpc.container_vpc.id
  cidr_block        = "10.0.6.0/24"
  availability_zone = "ap-northeast-1c"
  tags              = { Name = "container_db_az2" }
}

# Internet Gateway for dev environment
resource "aws_internet_gateway" "container_IGW" {
  vpc_id = aws_vpc.container_vpc.id
  tags   = { Name = "container_IGW" }
}

# Public Route Table for dev environment
resource "aws_route_table" "container_public_rtb" {
  vpc_id = aws_vpc.container_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.container_IGW.id
  }
  tags = { Name = "container_public_rtb" }
}

# Route Table Associations for public subnets
resource "aws_route_table_association" "public_az1" {
  subnet_id      = aws_subnet.container_public_az1.id
  route_table_id = aws_route_table.container_public_rtb.id
}

resource "aws_route_table_association" "public_az2" {
  subnet_id      = aws_subnet.container_public_az2.id
  route_table_id = aws_route_table.container_public_rtb.id
}

# Elastic IP for NAT Gateway
resource "aws_eip" "container_eip" {}

# NAT Gateway for dev environment
resource "aws_nat_gateway" "container_NGW" {
  subnet_id     = aws_subnet.container_public_az1.id
  allocation_id = aws_eip.container_eip.id
  tags          = { Name = "container_NGW" }
}

# Private Route Table for dev environment
resource "aws_route_table" "container_private_rtb" {
  vpc_id = aws_vpc.container_vpc.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.container_NGW.id
  }
  tags = { Name = "container_private_rtb" }
}

# Route Table Associations for private subnets
resource "aws_route_table_association" "private_az1" {
  subnet_id      = aws_subnet.container_private_az1.id
  route_table_id = aws_route_table.container_private_rtb.id
}

resource "aws_route_table_association" "private_az2" {
  subnet_id      = aws_subnet.container_private_az2.id
  route_table_id = aws_route_table.container_private_rtb.id
}

# Security Group for public instances (allow HTTP, HTTPS)
resource "aws_security_group" "container_public_sg" {
  vpc_id      = aws_vpc.container_vpc.id
  name        = "container_public_sg"
  description = "allow http, https"
  tags        = { Name = "container_public_sg" }
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
resource "aws_security_group" "container_private_sg" {
  vpc_id      = aws_vpc.container_vpc.id
  name        = "container_private_sg"
  description = "allow traffic from ELB Subnets"
  tags        = { Name = "container_private_sg" }
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.container_public_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
