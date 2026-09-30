# Jenkins Ubuntu Setup

This project is designed for a Linux/Ubuntu Jenkins agent.

## Required tools

- Git
- Python 3
- python3-venv
- Node.js + npm
- Docker CLI
- Docker daemon access for the Jenkins user

Verify:

```bash
git --version
python3 --version
node --version
npm --version
docker --version
```

If Jenkins is installed directly on an Ubuntu host:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

Verify Docker access:

```bash
sudo -u jenkins docker ps
```

If Jenkins runs inside a Docker container, configure Docker access for that container instead of using the host command above.

## Jenkins job

Use:

```text
Pipeline definition: Pipeline script from SCM
SCM: Git
Script Path: Jenkinsfile
```

GitHub webhook:

```text
https://<your-jenkins-domain>/github-webhook/
```

Never commit AWS credentials, database passwords, JWT secrets, or production secrets.

The AWS deployment phase will use Jenkins credentials and/or IAM roles.
