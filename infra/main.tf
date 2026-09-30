terraform { required_version=">= 1.6.0" required_providers { aws={source="hashicorp/aws",version="~> 6.0"} } }
provider "aws" { region=var.aws_region }
variable "aws_region" { default="ap-south-1" }
variable "project_name" { default="docuflow" }
output "project_name" { value=var.project_name }
