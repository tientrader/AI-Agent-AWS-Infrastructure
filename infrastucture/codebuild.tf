resource "aws_codebuild_project" "ai_ecs_dev" {
  name         = "ai-ecs-dev"
  description  = "Build project for AI ECS Dev"
  service_role = "arn:aws:iam::588738579043:role/service-role/codebuild-ecs-service-role"

  source {
    type            = "GITHUB"
    location        = "https://github.com/tientrader/AI-Agent-AWS-Infrastructure.git"
    git_clone_depth = 1
    buildspec       = "buildspec.yml"
  }

  source_version = "dev"

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux-x86_64-standard:5.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
  }

  artifacts {
    type = "NO_ARTIFACTS"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/aws/codebuild/ai-ecs-dev"
      stream_name = "build-log"
    }
  }
}

resource "aws_codebuild_webhook" "ai_ecs_dev_webhook" {
  project_name = aws_codebuild_project.ai_ecs_dev.name
}

resource "aws_codebuild_project" "ai_ecs_prod" {
  name         = "ai-ecs-prod"
  description  = "Build project for AI ECS Prod"
  service_role = "arn:aws:iam::588738579043:role/service-role/codebuild-ecs-service-role"

  source {
    type            = "GITHUB"
    location        = "https://github.com/tientrader/AI-Agent-AWS-Infrastructure.git"
    git_clone_depth = 1
    buildspec       = "buildspec.yml"
  }

  source_version = "main"

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux-x86_64-standard:5.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
  }

  artifacts {
    type = "NO_ARTIFACTS"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/aws/codebuild/ai-ecs-prod"
      stream_name = "build-log"
    }
  }
}

resource "aws_codebuild_webhook" "ai_ecs_prod_webhook" {
  project_name = aws_codebuild_project.ai_ecs_prod.name
}
