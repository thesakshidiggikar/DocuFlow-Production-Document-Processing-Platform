# DocuFlow

Production-oriented document processing SaaS.

## Local architecture

Browser -> Next.js -> FastAPI -> PostgreSQL
                              |-> S3-compatible storage (MinIO)
                              |-> SQS-compatible queue (ElasticMQ) -> Worker -> PostgreSQL

## Start

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000/docs
- MinIO console: http://localhost:9001

Production target: Route53/CloudFront -> ALB -> ECS/Fargate API -> RDS + Redis + S3 + SQS -> ECS/Fargate workers. Jenkins builds/tests Docker images and deploys through Pipeline-as-Code.


## Jenkins / Ubuntu

The included `Jenkinsfile` is written for a Linux/Ubuntu Jenkins agent and uses `sh`, `python3`, `npm`, and Docker CLI. See `docs/JENKINS_UBUNTU_SETUP.md` before configuring Jenkins.
