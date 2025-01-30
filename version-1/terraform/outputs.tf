# outputs.tf
output "instance_ids" {
  value = data.aws_instances.target_instances.ids
}

output "ssm_role_arn" {
  value = aws_iam_role.ssm_role.arn
}

output "instance_profile_arn" {
  value = aws_iam_instance_profile.ssm_profile.arn
}