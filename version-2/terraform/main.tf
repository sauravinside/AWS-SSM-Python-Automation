provider "aws" {
  region = var.aws_region
}

# IAM Role for SSM Access
resource "aws_iam_role" "ssm_role" {
  name = "SSMInstanceRole"

  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
  EOF
}

resource "aws_iam_policy_attachment" "ssm_policy_attachment" {
  name       = "ssm-policy-attachment"
  roles      = [aws_iam_role.ssm_role.name]
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm_profile" {
  name = "SSMInstanceProfile"
  role = aws_iam_role.ssm_role.name
}

# Attach IAM Role to Existing EC2 Instances
resource "aws_instance" "existing_instances" {
  for_each = toset(var.instance_ids)

  instance_id          = each.value
  iam_instance_profile = aws_iam_instance_profile.ssm_profile.name
}

output "ssm_enabled_instances" {
  value = var.instance_ids
}
