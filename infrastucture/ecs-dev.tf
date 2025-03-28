# --- 1. Create ECS Cluster ---
resource "aws_ecs_cluster" "tienaws_ecs" {
  name = "tienaws-ecs"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# --- 2. Create Task Definition for AI Agent ---
resource "aws_ecs_task_definition" "ai_agent_td" {
  family                   = "ai-agent-td"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "ai-agent"
      image     = "public.ecr.aws/k5o6t2c9/ai-agent:latest"
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]
    }
  ])
}

# --- 3. Create ECS Service for AI Agent ---
resource "aws_ecs_service" "ai_agent_service" {
  name            = "ai-agent"
  cluster         = aws_ecs_cluster.tienaws_ecs.id
  task_definition = aws_ecs_task_definition.ai_agent_td.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = [aws_subnet.container_private_az1.id, aws_subnet.container_private_az2.id]
    security_groups  = [aws_security_group.container_private_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ai_tg.arn
    container_name   = "ai-agent"
    container_port   = 8080
  }
}

# --- 4. IAM Role for ECS Task Execution ---
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
