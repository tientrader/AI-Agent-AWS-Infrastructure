resource "aws_codepipeline" "ai_ecs_dev" {
  name     = "ai-ecs-dev"
  role_arn = aws_iam_role.codepipeline_role.arn


  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.ecs_pro.arn
        FullRepositoryId = "tientrader/AI-Agent-AWS-Infrastructure"
        BranchName       = "dev"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = aws_codebuild_project.ai_ecs_dev.name
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      version         = "1"
      input_artifacts = ["build_output"]

      configuration = {
        ClusterName = "tienaws-ecs"
        ServiceName = "ai-agent"
        FileName    = "imagedefinitions.json"
      }
    }
  }
}

resource "aws_codepipeline" "ai_ecs_prod" {
  name     = "ai-ecs-prod"
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.ecs_pro.arn
        FullRepositoryId = "tientrader/AI-Agent-AWS-Infrastructure"
        BranchName       = "main"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = aws_codebuild_project.ai_ecs_prod.name
      }
    }
  }

  stage {
    name = "Approval"

    action {
      name     = "ApprovalProd"
      category = "Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"

      configuration = {
        NotificationArn    = aws_sns_topic.ai_aws_code_pipeline.arn
        CustomData         = "pls review"
        ExternalEntityLink = "https://dev.tienaws.click/"
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      version         = "1"
      input_artifacts = ["build_output"]

      configuration = {
        ClusterName = "tienaws-ecs"
        ServiceName = "ai-agent-prod"
        FileName    = "imagedefinitions.json"
      }
    }
  }
}

resource "aws_sns_topic" "ai_aws_code_pipeline" {
  name         = "ai-aws-code-pipeline"
  display_name = "ECS"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.ai_aws_code_pipeline.arn
  protocol  = "email"
  endpoint  = "ntien.se03@gmail.com"
}

resource "aws_s3_bucket" "pipeline_artifacts" {
  bucket        = "tienaws-pipeline-artifacts"
  force_destroy = true
}

resource "aws_codestarconnections_connection" "ecs_pro" {
  name          = "ecs-pro"
  provider_type = "GitHub"
}

resource "aws_iam_role" "codepipeline_role" {
  name = "codepipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "codepipeline.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "codepipeline_policy" {
  name        = "codepipeline-policy"
  description = "IAM policy for CodePipeline"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*",
          "codebuild:*",
          "codestar-connections:UseConnection",
          "ecs:*",
          "iam:PassRole"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codepipeline_attachment" {
  policy_arn = aws_iam_policy.codepipeline_policy.arn
  role       = aws_iam_role.codepipeline_role.name
}
