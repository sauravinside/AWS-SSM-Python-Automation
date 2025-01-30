# variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "target_tags" {
  description = "Tags to identify target instances"
  type        = map(string)
}

variable "ssm_role_name" {
  description = "Name of the IAM role for SSM"
  type        = string
  default     = "SSM-Instance-Role"
}

variable "ssm_profile_name" {
  description = "Name of the instance profile for SSM"
  type        = string
  default     = "SSM-Instance-Profile"
}