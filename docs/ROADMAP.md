# Production implementation

1. Local working application: API, frontend, PostgreSQL, MinIO, queue, worker.
2. AWS: ECR, ECS/Fargate API + worker, ALB, RDS PostgreSQL, ElastiCache Redis, S3, SQS + DLQ, CloudWatch, IAM, Secrets Manager.
3. Delivery: GitHub webhook -> Jenkinsfile -> test -> Docker build -> ECR -> Terraform/ECS deployment -> health check.
4. Hardening: private subnets, HTTPS, WAF, least privilege, vulnerability scanning, backups and rollback.
