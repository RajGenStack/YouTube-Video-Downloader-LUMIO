pipeline {
    agent any
    
    tools {
        jdk 'jdk17'
        nodejs 'node23'
    }
    
    environment {
        SCANNER_HOME = tool 'sonar-scanner'
        
        // Docker registry configuration
        REGISTRY = 'captainnoor1'
        
        // Service image names
        BACKEND_IMAGE = 'yt-downloader-backend'
        FRONTEND_IMAGE = 'yt-downloader-frontend'

        // Tag using build number
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

        stage('OWASP FS SCAN') {
            steps {
                dependencyCheck additionalArguments: '--scan ./ --disableYarnAudit --disableNodeAudit --update -n', odcInstallation: 'DP-Check'
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
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
                        // Tag and Push Backend
                        sh "docker tag ${BACKEND_IMAGE} ${REGISTRY}/${BACKEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker tag ${BACKEND_IMAGE} ${REGISTRY}/${BACKEND_IMAGE}:latest"
                        sh "docker push ${REGISTRY}/${BACKEND_IMAGE}:${IMAGE_TAG}"
                        sh "docker push ${REGISTRY}/${BACKEND_IMAGE}:latest"

                        // Tag and Push Frontend
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
                        # Install Docker Scout CLI directly
                        curl -sSfL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh \
                          | sh -s -- -b /usr/local/bin

                        # Login to Docker Hub for Scout
                        echo $DOCKER_PASSWORD | docker login -u captainnoor1 --password-stdin

                        # Run Scout scans
                        docker scout cves captainnoor1/yt-downloader-backend:latest --exit-code --only-severity critical,high
                        docker scout cves captainnoor1/yt-downloader-frontend:latest --exit-code --only-severity critical,high
                    '''
                }
            }
        }
        
        stage("Deploy to Container") {
            steps {
                echo "Deploying applications with Docker Compose..."
                sh "docker-compose -f docker-compose.prod.yml down"
                sh "docker-compose -f docker-compose.prod.yml up -d"
            }
        }
    }
    
    post {
        always {
            // Clean up workspace dangling Docker layers to save space
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
