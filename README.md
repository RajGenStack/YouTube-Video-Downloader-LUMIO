# YouTube Downloader

Organised repository for the Lumio YouTube downloader app.

## Structure

- `frontend/` — Static frontend site and client assets.
- `backend/` — FastAPI downloader API and deployment config.
- `docker-compose.yml` — Local Docker orchestration for frontend + backend.

## Local setup

### 1. Start the full stack with Docker

```powershell
cd "c:\Users\sarah\Desktop\yt downloader"
docker compose up --build
```

Frontend: `http://localhost:3000`
Backend: `http://localhost:8000`

### 2. Frontend only

```powershell
cd frontend
docker build -t lumio-frontend .
docker run --rm -p 3000:80 lumio-frontend
```

### 3. Backend only

```powershell
cd backend
cp .env.example .env
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Notes

- Update `frontend/js/app.js` to point `downloadApiEndpoint` at your backend URL.
- Backend Docker config includes FFmpeg and production-ready packaging.
- Use `backend/README.md` for backend-specific documentation.

## CI/CD Jenkins Pipeline

We have configured a declarative [Jenkinsfile](file:///c:/Users/sarah/Desktop/yt%20downloader/Jenkinsfile) at the root of the repository to automate testing, security scanning, image registry uploads, and containerized deployment.

### Pipeline Stages
1. **Clean Workspace**: Wipes files from previous builds.
2. **Git Checkout**: Pulls code from repository.
3. **Sonarqube Analysis**: Runs static code analysis via SonarQube.
4. **Code Quality Gate**: Validates metrics against your SonarQube server's Quality Gate thresholds.
5. **OWASP FS SCAN**: Performs Software Composition Analysis (SCA) on dependencies.
6. **Trivy File Scan**: Scans source files and locks for CVEs (reports are saved to `trivy.txt` and emailed).
7. **Build Docker Image**: Compiles backend and frontend production Docker images.
8. **Tag & Push to DockerHub**: Pushes both images with dynamic builds and `latest` tags to `captainnoor1` Docker Hub registry.
9. **Docker Scout Image**: Scans the compiled images for critical and high vulnerabilities using Docker Scout.
10. **Deploy to Container**: Re-deploys containers using `docker-compose.prod.yml` to expose the application publicly.
11. **Post Notifications**: Automatically emails build details and attaches the filesystem scan results (`trivy.txt`).

### Prerequisites & Jenkins Configuration
Ensure the following settings are configured on your Jenkins Controller/Agent:

#### 1. Installed Plugins
*   **Pipeline**
*   **Credentials Binding**
*   **SonarQube Scanner**
*   **OWASP Dependency-Check**
*   **Email Extension (emailext)**

#### 2. Configured Credentials
*   `docker`: Username and Password for Docker Hub (`captainnoor1`).
*   `Sonar-token`: Credentials token for authenticating to SonarQube.

#### 3. Configured Tools (Global Tool Configuration)
*   **JDK**: Named `jdk17`.
*   **Node.js**: Named `node23`.
*   **SonarQube Scanner**: Named `sonar-scanner`.
*   **Dependency-Check**: Named `DP-Check`.
*   **SonarQube Server**: Configured under System Settings named `sonar-server`.

