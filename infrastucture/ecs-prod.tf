# --- 1. Create ECS Cluster for Production ---
resource "aws_ecs_cluster" "tienaws_ecs_prod" {
  name = "tienaws-ecs-prod"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# --- 2. Create ECS Service for AI Agent in Production ---
resource "aws_ecs_service" "ai_agent_service_prod" {
  name            = "ai-agent-prod"
  cluster         = aws_ecs_cluster.tienaws_ecs_prod.id
  task_definition = "ai-agent-td"
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = [aws_subnet.container_private_az1_prod.id, aws_subnet.container_private_az2_prod.id]
    security_groups  = [aws_security_group.container_private_sg_prod.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ai_tg_prod.arn
    container_name   = "ai-agent"
    container_port   = 8080
  }
}
