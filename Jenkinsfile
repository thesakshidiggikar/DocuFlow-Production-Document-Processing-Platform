pipeline {
    agent any

    environment {
        IMAGE_NAME = "docuflow-api"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Environment Check') {
            steps {
                sh '''
                    set -eux
                    uname -a
                    git --version
                    python3 --version
                    node --version
                    npm --version
                    docker --version
                '''
            }
        }

        stage('Backend Validation') {
            steps {
                sh '''
                    set -eux
                    python3 -m venv .ci-venv
                    . .ci-venv/bin/activate
                    python -m pip install --upgrade pip
                    python -m pip install -r backend/requirements.txt
                    python -m compileall backend/app
                '''
            }
        }

        stage('Frontend Build') {
            steps {
                sh '''
                    set -eux
                    cd frontend
                    if [ -f package-lock.json ]; then
                        npm ci
                    else
                        npm install
                    fi
                    npm run build
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    set -eux
                    docker build -t "${IMAGE_NAME}:ci" ./backend
                '''
            }
        }

        stage('Deployment Gate') {
            steps {
                echo 'CI validation passed.'
                echo 'AWS deployment will be added with ECR + ECS/Fargate infrastructure.'
            }
        }
    }

    post {
        always {
            sh 'rm -rf .ci-venv'
            echo "Pipeline completed with result: ${currentBuild.currentResult}"
        }
    }
}
