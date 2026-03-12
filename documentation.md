# 📄 CloudHelm Setup & Documentation Guide

Welcome to the comprehensive setup guide for **CloudHelm**. This document will walk you through everything from cloning the repository to running the full stack with Docker Compose and Observability.

## 🌟 Project Overview
**CloudHelm** is a unified operations platform designed for multi-cloud infrastructure management. It provides engineering teams with real-time insights into cloud spending, resource utilization, application performance, and operational incidents across AWS, GCP, and Azure environments.

The platform integrates advanced AI assistants to help with debugging, security scanning, and automated incident summarization, ensuring that your cloud infrastructure remains efficient, secure, and cost-effective.

## 🛠️ Tech Stack

### Frontend
- **React 18** with **TypeScript**
- **Vite** (Build Tool)
- **Tailwind CSS** & **Shadcn UI** (Styling)
- **Lucide React** (Icons)
- **Recharts** (Data Visualization)

### Backend
- **FastAPI** (High-performance Python framework)
- **SQLAlchemy 2.0** (ORM)
- **Alembic** (Database Migrations)
- **Pydantic v2** (Data Validation)
- **Uvicorn** (ASGI Server)

### AI & Observability
- **Google Gemini 2.5 Flash** (Incident Summaries)
- **Mistral AI** (CloudHelm Assistant CLI)
- **Prometheus** (Metrics Collection)
- **Grafana** (Visualization Dashboards)
- **OpenTelemetry** & **Tempo** (Distributed Tracing)

### Infrastructure & DevOps
- **Docker & Docker Compose** (Containerization)
- **PostgreSQL** (Database)
- **Neon** (Serverless DB Hosting)

---

## 🏗️ Table of Contents
1. [Prerequisites](#-prerequisites)
2. [Step 1: Clone the Repository](#-step-1-clone-the-repository)
3. [Step 2: External Services Setup](#-step-2-external-services-setup)
4. [Step 3: Local Backend Setup](#-step-4-local-backend-setup)
5. [Step 4: Local Frontend Setup](#-step-5-local-frontend-setup)
6. [Step 5: Running Locally (Dev Mode)](#-step-6-running-locally-dev-mode)
7. [Step 6: Docker Deployment (Full Stack)](#-step-7-docker-deployment-full-stack)
8. [🔍 Accessing Services](#-accessing-services)
9. [❓ Troubleshooting](#-troubleshooting)

---

## 🛠️ Prerequisites

Ensure you have the following installed on your system:
- **Python 3.12+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**
- **PostgreSQL** (Optional if using Docker or Neon DB)

---

## 📂 Step 1: Clone the Repository

Open your terminal and run:
```bash
git clone https://github.com/Dakshmulundkar/CloudHelm.git
cd CloudHelm
```

---

## 🌐 Step 2: External Services Setup

CloudHelm relies on several external services for its core features:

### 1. Database (Neon.tech - Recommended)
1. Sign up at [Neon.tech](https://neon.tech).
2. Create a new project and copy your connection string.
3. Remember to add `+psycopg` to the URL.
   - *Example:* `postgresql+psycopg://user:pass@ep-stack-name.region.neon.tech/neondb`

### 2. OAuth Credentials (Required for Login)
- **GitHub:** Create an OAuth app at [GitHub Developer Settings](https://github.com/settings/developers).
  - Homepage URL: `http://localhost:5173`
  - Callback URL: `http://localhost:8000/auth/github/callback`
- **Google:** Create Credentials at [Google Cloud Console](https://console.cloud.google.com/).
  - Callback URL: `http://localhost:8000/auth/google/callback`

### 3. AI Services (Optional for Assistant Features)
- **Gemini AI:** Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey).
- **Mistral AI:** Get an API key from [Mistral Console](https://console.mistral.ai/).

---

## ⚙️ Step 3: Local Backend Setup

1. **Create and Activate Virtual Environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the `backend/` directory:
   ```env
   DATABASE_URL=your_postgresql_url
   JWT_SECRET=your_32_char_secret
   GITHUB_CLIENT_ID=your_id
   GITHUB_CLIENT_SECRET=your_secret
   GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
   GOOGLE_CLIENT_ID=your_id
   GOOGLE_CLIENT_SECRET=your_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
   GEMINI_API_KEY=your_key
   MISTRAL_API_KEY=your_key
   ```

4. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```

---

## 🎨 Step 4: Local Frontend Setup

1. **Install Dependencies:**
   ```bash
   cd ../frontend
   npm install
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the `frontend/` directory:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

---

## 🚀 Step 5: Running Locally (Dev Mode)

### Start Backend
```bash
cd backend
python -m uvicorn main:app --reload
```
*Runs at: http://localhost:8000*

### Start Frontend
```bash
cd frontend
npm run dev
```
*Runs at: http://localhost:5173*

---

## 🐳 Step 6: Docker Deployment (Full Stack)

CloudHelm uses multiple Docker Compose files to manage different aspects of the system.

### 1. Main App + Monitoring (Prometheus & Grafana)
This starts the backend, frontend, database, and the monitoring stack.
```bash
docker compose -f docker-compose.monitoring.yml up --build -d
```

### 2. Observability Stack (OpenTelemetry & Tempo)
This starts the tracing infrastructure.
```bash
docker compose -f docker-compose.observability.yml up -d
```

### 3. Stop All Services
```bash
docker compose -f docker-compose.observability.yml down
docker compose -f docker-compose.monitoring.yml down
```

---

## 🔍 Accessing Services

| Service | URL | Note |
| :--- | :--- | :--- |
| **CloudHelm Frontend** | http://localhost:5173 | Core Dashboard |
| **Backen API (Swagger)** | http://localhost:8000/docs | API Documentation |
| **Grafana** | http://localhost:4000 | Default user: `admin` / `admin` |
| **Prometheus** | http://localhost:9091 | Raw Metrics |
| **Tempo (Tracing)** | http://localhost:3200 | Internal Tracing Data |

---

## ❓ Troubleshooting

### 1. Database Connection Error
- Ensure your `DATABASE_URL` has `+psycopg` for SQLAlchemy compatibility.
- Check if your IP is allowlisted in the Neon DB console.

### 2. OAuth Login Fails
- Double-check the Callback URL in your GitHub/Google app settings. It must match the `.env` exactly.

### 3. AI Features Not Working
- Ensure you have valid `GEMINI_API_KEY` and `MISTRAL_API_KEY` in the `backend/.env`.

### 4. Port Conflicts
- Ensure ports `8000`, `5173`, `4000`, and `9091` are not being used by other applications.

---

Built with ❤️ for Cloud Excellence.
