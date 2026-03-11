# CloudHelm

**Cloud Operations Platform for Multi-Cloud Infrastructure Management**

CloudHelm is a unified platform that provides real-time insights into cloud spending, resource utilization, application performance, and operational incidents across AWS, GCP, and Azure environments.

---

## 🚀 Quick Start

**Total Monthly Cost: $0** ✨

1. [Neon Database](https://neon.tech) - Free serverless PostgreSQL (no credit card)
2. [GitHub OAuth](https://github.com/settings/developers) - Free authentication
3. [Google OAuth](https://console.cloud.google.com) - Free authentication (optional)
4. Generate JWT secret: `openssl rand -hex 32`

---

## Features

### 💰 Cost Radar
- Multi-cloud cost tracking (AWS, GCP, Azure)
- Real-time cost aggregation by team, service, and environment
- ML-powered anomaly detection for unusual spending patterns
- Linear regression forecasting for future costs
- Budget tracking with status monitoring and alerts

### 📊 Resource Efficiency
- Track resource utilization across compute, storage, and network
- Identify underutilized resources and optimization opportunities
- Right-sizing recommendations based on actual usage patterns
- Waste score analysis and cost-saving suggestions

### 🏥 Application Health
- Monitor application performance metrics and SLOs
- Track error rates, latency, and availability
- Docker and Kubernetes integration
- Real-time anomaly detection
- Service health dashboards

### 🚨 Incident Management
- Track and manage production incidents
- AI-powered incident summaries (Gemini 2.5 Flash)
- Correlate incidents with releases and deployments
- Incident timeline and resolution tracking

### 🚀 Release Impact Analysis
- GitHub integration for release tracking
- Risk scoring for deployments
- Release history and impact analysis
- Correlation with incidents and performance

### 🤖 CloudHelm Assistant
- AI-powered code analysis (Mistral AI)
- CLI commands for testing and debugging
  - `/test` - Run tests
  - `/lint` - Check code quality
  - `/errors` - Find compilation errors
  - `/build` - Run build commands
  - `/run <command>` - Execute safe shell commands
  - `/help` - Show all commands
- Security vulnerability scanning
- Incident solution suggestions
- Interactive chat interface

---

## Prerequisites

- **Python 3.12+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **PostgreSQL** - Database (Neon free tier recommended)
- **Git** - Version control

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Dakshmulundkar/CloudHelm.git
cd CloudHelm
```

### 2. Setup Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Setup Database (Neon - Free Tier)

a. **Create Neon account**
   - Go to [https://neon.tech](https://neon.tech)
   - Sign up (use GitHub, Google, or email)

b. **Create a project**
   - Project name: `cloudhelm`
   - PostgreSQL version: 16 (latest)
   - Region: Choose closest to you
   - Click "Create project"

c. **Copy your connection string**
   - After creation, copy the connection string
   - Format: `postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require`

d. **Modify for SQLAlchemy**
   - Add `+psycopg` after `postgresql`:
   - `postgresql+psycopg://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require`

### 6. Configure Environment Variables

**Backend configuration:**

```bash
cd backend
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `backend/.env`:

```env
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql+psycopg://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require

# General
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_ORIGIN=http://localhost:5173

# JWT
JWT_SECRET=your-super-secret-key-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
GITHUB_TOKEN=your_github_personal_access_token  # Optional

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# AI Services (Optional)
GEMINI_API_KEY=your_gemini_api_key  # For incident summaries
MISTRAL_API_KEY=your_mistral_api_key  # For CloudHelm Assistant
```

**Frontend configuration:**

```bash
cd frontend
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 7. Setup OAuth Credentials

**GitHub OAuth:**
- Go to https://github.com/settings/developers
- Click "New OAuth App"
- Application name: `CloudHelm Dev`
- Homepage URL: `http://localhost:5173`
- Authorization callback URL: `http://localhost:8000/auth/github/callback`
- Copy Client ID and Client Secret to `backend/.env`

**Google OAuth:**
- Go to https://console.cloud.google.com/
- Create a new project or select existing
- Navigate to "APIs & Services" > "Credentials"
- Click "Create Credentials" > "OAuth 2.0 Client ID"
- Application type: Web application
- Authorized redirect URI: `http://localhost:8000/auth/google/callback`
- Copy Client ID and Client Secret to `backend/.env`

### 8. Run Database Migrations

```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Navigate to backend directory
cd backend

# Run migrations
alembic upgrade head

# Return to project root
cd ..
```

---

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
cd backend
python -m uvicorn main:app --reload
```

Backend will run on: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend will run on: http://localhost:5173

### Using Docker

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

---

## AI Services Configuration

### Gemini AI (Incident Summaries)

- **Model**: `gemini-2.0-flash-exp` (Gemini 2.5 Flash)
- **Purpose**: Generate AI-powered incident summaries
- **Get API Key**: https://makersuite.google.com/app/apikey
- **Setup**: Add `GEMINI_API_KEY` to `backend/.env`

### Mistral AI (CloudHelm Assistant)

- **Model**: `mistral-large-latest`
- **Purpose**: Code analysis, incident solutions, security reviews
- **Get API Key**: https://console.mistral.ai/
- **Setup**: Add `MISTRAL_API_KEY` to `backend/.env`
- **Features**:
  - Interactive chat for code analysis
  - CLI commands: `/test`, `/lint`, `/errors`, `/build`, `/run`
  - Execute tests and find errors directly from chat
  - Security vulnerability scanning

**Both services are optional** - the application works without them.

---

## CloudHelm Assistant CLI Commands

The assistant supports CLI-like commands for testing and debugging:

```bash
/help                    # Show all available commands
/test [path]             # Run tests in repository
/lint [path]             # Run linter to check code quality
/errors [path]           # Find compilation/syntax errors
/build [target]          # Run build command
/run <command>           # Execute safe shell commands
```

**Examples:**
```bash
/test                    # Run all tests
/lint src/               # Lint specific directory
/errors backend/         # Check backend for errors
/run git status          # Check git status
/run npm install         # Install dependencies
```

**Security**: Only safe commands are allowed (npm, python, pytest, eslint, tsc, git, ls, dir, cat, type)

---

## Deployment

CloudHelm can be deployed to production using free tier services:

- **Backend**: Render (Free tier)
- **Frontend**: Netlify or Vercel (Free tier)
- **Database**: Neon PostgreSQL (Free tier)

**Total Monthly Cost: $0** ✨

### Quick Deploy

1. **Deploy Backend to Render**
   - Connect GitHub repository
   - Set environment variables
   - Deploy automatically

2. **Deploy Frontend to Netlify/Vercel**
   - Connect GitHub repository
   - Set `VITE_API_BASE_URL`
   - Deploy automatically

3. **Update OAuth Redirect URIs**
   - Update GitHub OAuth callback URL
   - Update Google OAuth callback URL

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

For step-by-step checklist, see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

## Project Structure

```
CloudHelm/
├── backend/                 # FastAPI backend
│   ├── core/               # Configuration and security
│   ├── models/             # SQLAlchemy models
│   ├── routers/            # API endpoints
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── migrations/         # Alembic migrations
│   ├── main.py            # Application entry point
│   └── requirements.txt   # Python dependencies
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── types/         # TypeScript types
│   │   ├── lib/           # Utilities and API client
│   │   └── context/       # React context
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite configuration
├── docker-compose.yml     # Docker configuration
└── README.md             # This file
```

---

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Common Commands

### Backend

```bash
# Run development server
python -m uvicorn main:app --reload

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1

# Check current migration
alembic current
```

### Frontend

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

---

## Environment Variables

### Required Backend Variables

```env
DATABASE_URL              # PostgreSQL connection string
JWT_SECRET               # Secret key for JWT tokens
FRONTEND_ORIGIN          # Frontend URL for CORS
GITHUB_CLIENT_ID         # GitHub OAuth client ID
GITHUB_CLIENT_SECRET     # GitHub OAuth client secret
GITHUB_REDIRECT_URI      # GitHub OAuth callback URL
GOOGLE_CLIENT_ID         # Google OAuth client ID
GOOGLE_CLIENT_SECRET     # Google OAuth client secret
GOOGLE_REDIRECT_URI      # Google OAuth callback URL
```

### Optional Backend Variables

```env
GEMINI_API_KEY          # For AI-powered incident summaries
MISTRAL_API_KEY         # For CloudHelm Assistant
GITHUB_TOKEN            # Personal access token for release tracking
```

### Frontend Variables

```env
VITE_API_BASE_URL       # Backend API URL
```

---

## Troubleshooting

### Database Connection Issues

**Problem**: Cannot connect to database

**Solution**:
1. Verify DATABASE_URL is correct in `backend/.env`
2. Ensure `+psycopg` is added after `postgresql`
3. Check `?sslmode=require` is at the end
4. Verify Neon database is active

### OAuth Issues

**Problem**: OAuth login fails

**Solution**:
1. Verify OAuth credentials in `backend/.env`
2. Check redirect URIs match exactly
3. Ensure OAuth app is not suspended
4. Clear browser cookies and try again

### Port Already in Use

**Problem**: Port 8000 or 5173 already in use

**Solution**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Module Not Found

**Problem**: Python module not found

**Solution**:
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r backend/requirements.txt
```

---

## Security Best Practices

### API Keys
- ✅ Store all API keys in `.env` files
- ✅ Never commit `.env` files to version control
- ✅ Use different keys for dev/staging/prod
- ✅ Rotate API keys regularly (every 90 days)

### Database
- ✅ Use strong passwords
- ✅ Enable SSL/TLS connections
- ✅ Restrict database access by IP
- ✅ Regular backups

### Authentication
- ✅ Use strong JWT secrets (min 32 characters)
- ✅ Enable 2FA for OAuth providers
- ✅ Set appropriate token expiration times
- ✅ Implement rate limiting

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Copyright (c) 2024 Daksh Mulundkar. All rights reserved.

This software and associated documentation files are proprietary and confidential. Unauthorized copying, modification, distribution, or use of this software, via any medium, is strictly prohibited without explicit written permission from the copyright holder.

---

## Contact

**Daksh Mulundkar**
- GitHub: [@Dakshmulundkar](https://github.com/Dakshmulundkar)
- Repository: [CloudHelm](https://github.com/Dakshmulundkar/CloudHelm)

For questions, issues, or collaboration inquiries, please open an issue on GitHub.

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- Database hosted on [Neon](https://neon.tech/)
- AI powered by [Google Gemini](https://ai.google.dev/) and [Mistral AI](https://mistral.ai/)
- UI components styled with [Tailwind CSS](https://tailwindcss.com/)
