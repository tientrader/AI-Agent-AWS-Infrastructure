# --- 1. Create ALB (Application Load Balancer) ---
resource "aws_lb" "ecs_alb_prod" {
  name                             = "ecs-alb-prod"
  internal                         = false
  load_balancer_type               = "application"
  security_groups                  = [aws_security_group.container_public_sg_prod.id]
  subnets                          = [aws_subnet.container_public_az1_prod.id, aws_subnet.container_public_az2_prod.id]
  enable_deletion_protection       = false
  enable_cross_zone_load_balancing = true

  tags = {
    Name = "ecs-alb-prod"
  }
}

# --- 2. Create Target Group for ALB ---
resource "aws_lb_target_group" "ai_tg_prod" {
  name        = "ai-tg-prod"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = aws_vpc.container_vpc_prod.id
  target_type = "ip"

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  tags = {
    Name = "ai-tg-prod"
  }
}

# --- 3. Create Route 53 Record ---
resource "aws_route53_record" "prod_record" {
  zone_id = data.aws_route53_zone.tienaws_click.zone_id
  name    = "www.tienaws.click"
  type    = "A"
  alias {
    name                   = aws_lb.ecs_alb_prod.dns_name
    zone_id                = aws_lb.ecs_alb_prod.zone_id
    evaluate_target_health = true
  }
}

# --- 4. Create ACM Certificate Request ---
resource "aws_acm_certificate" "prod_cert" {
  domain_name       = "www.tienaws.click"
  validation_method = "DNS"

  tags = {
    Name = "www.tienaws.click"
  }
}

# --- 5. Create DNS Validation Record for ACM ---
resource "aws_route53_record" "prod_cert_validation" {
  for_each = { for dvo in aws_acm_certificate.prod_cert.domain_validation_options : dvo.domain_name => dvo }

  zone_id = data.aws_route53_zone.tienaws_click.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  ttl     = 60
  records = [each.value.resource_record_value]
}

# --- 6. Request ACM Certificate Validation ---
resource "aws_acm_certificate_validation" "prod_cert_validation" {
  certificate_arn         = aws_acm_certificate.prod_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.prod_cert_validation : record.fqdn]
}

# --- 7. Create HTTPS Listener for ALB ---
resource "aws_lb_listener" "https_listener_prod" {
  load_balancer_arn = aws_lb.ecs_alb_prod.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.prod_cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ai_tg_prod.arn
  }
}

# --- 8. Create HTTP Listener for ALB with Redirect to HTTPS ---
resource "aws_lb_listener" "http_listener_prod" {
  load_balancer_arn = aws_lb.ecs_alb_prod.arn
  port              = 8080
  protocol          = "HTTP"
  default_action {
    type = "redirect"
    redirect {
      protocol    = "HTTPS"
      port        = "443"
      status_code = "HTTP_301"
    }
  }
}
