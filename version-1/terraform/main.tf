# main.tf
provider "aws" {
  region = var.aws_region
}

# Create IAM role for SSM
resource "aws_iam_role" "ssm_role" {
  name = "SSM-Instance-Role"

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
}

# Attach SSM policy to role
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Create instance profile
resource "aws_iam_instance_profile" "ssm_profile" {
  name = "SSM-Instance-Profile"
  role = aws_iam_role.ssm_role.name
}

# Get existing instances by tags
data "aws_instances" "target_instances" {
  instance_tags = var.target_tags
}