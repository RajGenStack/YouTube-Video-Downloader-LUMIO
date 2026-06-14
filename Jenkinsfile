pipeline {
    agent any
    
    tools {
        jdk 'jdk17'
        nodejs 'node23'
    }
    
    environment {
        SCANNER_HOME = tool 'sonar-scanner'
        REGISTRY = 'captainnoor1'
        BACKEND_IMAGE = 'yt-downloader-backend'
        FRONTEND_IMAGE = 'yt-downloader-frontend'
        IMAGE_TAG = "build-${env.BUILD_NUMBER}"
    }
    
    stages {
        stage("clean workspace") {
            steps {
                cleanWs()
            }
        }
        
        stage("Git Checkout") {
            steps {
                git branch: 'main', url: 'https://github.com/RajGenStack/YouTube-Video-Downloader-LUMIO.git'
            }
        }
        
        stage("Sonarqube Analysis") {
            steps {
                withSonarQubeEnv('sonar-server') {
                    sh " \$SCANNER_HOME/bin/sonar-scanner -Dsonar.projectName=yt-downloader -Dsonar.projectKey=yt-downloader "
                }
            }
        }
        
        stage("Code Quality Gate") {
            steps {
                script {
                    waitForQualityGate abortPipeline: false, credentialsId: 'Sonar-token' 
                }
            } 
        }
        
        stage("Trivy File Scan") {
            steps {
                sh "trivy fs . > trivy.txt"
            }
        }
        
        stage("Build Docker Image") {
            steps {
                echo "Building Docker images for Backend and Frontend..."
                sh "docker build -t ${BACKEND_IMAGE} -f backend/Dockerfile backend/"
                sh "docker build -t ${FRONTEND_IMAGE} -f frontend/Dockerfile frontend/"
            }
        }
        
        stage("Tag & Push to DockerHub") {
            steps {
                script {
                    withDockerRegistry(credentialsId: 'docker') {
                        sh "docker tag ${BACKEND_IMAGE} ${REGISTRY}/${BACKEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker tag ${BACKEND_IMAGE} ${REGISTRY}/${BACKEND_IMAGE}:latest"
                        sh "docker push ${REGISTRY}/${BACKEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker push ${REGISTRY}/${BACKEND_IMAGE}:latest"

                        sh "docker tag ${FRONTEND_IMAGE} ${REGISTRY}/${FRONTEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker tag ${FRONTEND_IMAGE} ${REGISTRY}/${FRONTEND_IMAGE}:latest"
                        sh "docker push ${REGISTRY}/${FRONTEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker push ${REGISTRY}/${FRONTEND_IMAGE}:latest"
                    }
                }
            }
        }
        
        stage('Docker Scout Image') {
            steps {
                withDockerRegistry(credentialsId: 'docker', url: 'https://index.docker.io/v1/') {
                    sh '''
                        docker scout cves captainnoor1/yt-downloader-backend:latest
                        docker scout cves captainnoor1/yt-downloader-frontend:latest
                        docker scout recommendations captainnoor1/yt-downloader-backend:latest
                        docker scout recommendations captainnoor1/yt-downloader-frontend:latest
                    '''
                }
            }
        }
        
        stage("Deploy to Container") {
            steps {
                echo "Deploying applications with Docker Compose..."
                sh "docker-compose -f docker-compose.prod.yml down || true"
                sh "docker-compose -f docker-compose.prod.yml up -d"
            }
        }
    }
    
    post {
        always {
            sh "docker image prune -f"
            
            emailext attachLog: true,
                subject: "'${currentBuild.result}'",
                body: """
                    <html>
                    <body>
                        <div style="background-color: #FFA07A; padding: 10px; margin-bottom: 10px;">
                            <p style="color: white; font-weight: bold;">Project: ${env.JOB_NAME}</p>
                        </div>
                        <div style="background-color: #90EE90; padding: 10px; margin-bottom: 10px;">
                            <p style="color: white; font-weight: bold;">Build Number: ${env.BUILD_NUMBER}</p>
                        </div>
                        <div style="background-color: #87CEEB; padding: 10px; margin-bottom: 10px;">
                            <p style="color: white; font-weight: bold;">URL: ${env.BUILD_URL}</p>
                        </div>
                    </body>
                    </html>
                """,
                to: 'tomholland1953sm@gmail.com',
                mimeType: 'text/html',
                attachmentsPattern: 'trivy.txt'
        }
    }
}
