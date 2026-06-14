pipeline {
    agent any

    environment {
        // Docker registry configuration (e.g., Docker Hub)
        REGISTRY = 'captainnoor1'
        DOCKER_CREDS_ID = 'docker-hub-credentials' // Jenkins Credential ID for Docker Hub username/password

        // Service image names
        BACKEND_IMAGE = 'yt-downloader-backend'
        FRONTEND_IMAGE = 'yt-downloader-frontend'

        // Tag using build number, default to latest as secondary tag
        IMAGE_TAG = "build-${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout code from Git repository
                checkout scm
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    echo "Running SonarQube static code analysis..."
                    // Requires the 'SonarQube Scanner' plugin and server configured under system settings
                    withSonarQubeEnv('SonarQubeServer') {
                        // Requires 'sonar-scanner' CLI tool configured under Global Tool Configuration
                        def sonarScanner = tool name: 'sonar-scanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                        sh "${sonarScanner} -Dsonar.projectKey=yt-downloader -Dsonar.sources=."
                    }
                }
            }
        }

        stage('OWASP Dependency-Check') {
            steps {
                script {
                    echo "Running OWASP Dependency-Check dependency scanner..."
                    // Requires 'dependency-check' configured under Global Tool Configuration
                    def dependencyCheckTool = tool name: 'dependency-check', type: 'org.jenkinsci.plugins.DependencyCheck.DependencyCheckToolInstallation'
                    
                    // Execute OWASP scan
                    sh "${dependencyCheckTool} --scan ./ --out ./dependency-check-report.xml --format XML --format HTML"
                    
                    // Publish Dependency-Check XML results to the Jenkins build report page
                    dependencyCheckPublisher pattern: 'dependency-check-report.xml'
                }
            }
        }

        stage('Trivy Filesystem Scan') {
            steps {
                echo "Running Trivy filesystem security scanning..."
                // Scan workspace repository filesystem for security vulnerabilities
                sh "trivy fs --severity HIGH,CRITICAL --format table ."
            }
        }

        stage('Build Images') {
            steps {
                echo "Building Docker images..."
                // Build Backend image
                sh "docker build -t ${REGISTRY}/${BACKEND_IMAGE}:${IMAGE_TAG} -t ${REGISTRY}/${BACKEND_IMAGE}:latest -f backend/Dockerfile backend/"
                // Build Frontend image
                sh "docker build -t ${REGISTRY}/${FRONTEND_IMAGE}:${IMAGE_TAG} -t ${REGISTRY}/${FRONTEND_IMAGE}:latest -f frontend/Dockerfile frontend/"
            }
        }

        stage('Trivy Image Scan') {
            steps {
                echo "Running Trivy image vulnerability scanning..."
                // Scan the newly built Docker images before they are pushed to the registry
                sh "trivy image --severity HIGH,CRITICAL --format table ${REGISTRY}/${BACKEND_IMAGE}:${IMAGE_TAG}"
                sh "trivy image --severity HIGH,CRITICAL --format table ${REGISTRY}/${FRONTEND_IMAGE}:${IMAGE_TAG}"
            }
        }

        stage('Push Images') {
            steps {
                script {
                    echo "Logging into Docker registry and pushing images..."
                    // Login to Docker Hub using credentials stored in Jenkins
                    withCredentials([usernamePassword(credentialsId: env.DOCKER_CREDS_ID, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin"
                        
                        // Push Backend tags
                        sh "docker push ${REGISTRY}/${BACKEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker push ${REGISTRY}/${BACKEND_IMAGE}:latest"

                        // Push Frontend tags
                        sh "docker push ${REGISTRY}/${FRONTEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker push ${REGISTRY}/${FRONTEND_IMAGE}:latest"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying applications with Docker Compose..."
                // Deploy locally or on target machine (run production docker-compose configuration)
                // Note: If deploying to a remote host, configure an SSH Agent or remote Docker context
                sh "docker-compose -f docker-compose.prod.yml down"
                sh "docker-compose -f docker-compose.prod.yml up -d"
            }
        }
    }

    post {
        always {
            echo "Cleaning up local workspace build artifacts and dangling Docker layers..."
            // Prune dangling images to conserve agent disk space
            sh "docker image prune -f"
        }
        success {
            echo "Pipeline built and deployed successfully!"
        }
        failure {
            echo "Pipeline execution failed. Check console output for debugging."
        }
    }
}
