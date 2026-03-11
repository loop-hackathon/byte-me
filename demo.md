# CloudHelm Overview

## ✅ Working Features
* **Trivy Security Scanning:** Trivy is fully running — performs container vulnerability scanning and returns detailed diagnostics including severity levels, CVE IDs, descriptions, and links to advisories.
* **Incident Management:** AI-powered incident summaries, timeline tracking, and incident diagnostics powered by Trivy scan results.
* **SBOM (Software Bill of Materials):** Users can view SBOM details directly in the UI or download the full SBOM as a JSON file for offline analysis and compliance.
* **Tenant Isolation:** Robust user isolation and multi-tenancy support.
* **Application Health:** End-to-end performance and latency monitoring with Docker/K8s integration.
* **Release Impact Analysis:** Deployment risk scoring, GitHub release correlation, and integrated vulnerability & SBOM data per release.
* **CloudHelm Assistant:** Mistral AI CLI coding assistant `/test`, `/lint`, `/run` inside the app.

## 🚧 Features Not Yet Implemented
* **Live MTTR (Mean Time to Recovery):** Real-time MTTR calculation and tracking is not yet available.
* **Live Incident Auto-Resolution:** Automated incident remediation workflows are planned but not implemented.
* **Cost & Resource Efficiency Dashboard:** Cost analysis and resource optimization page is under development.
* **Real-Time Alerting:** Push-based alerting and notification pipelines are not yet integrated.

## ⚠️ Known Issues & Limitations
* **Costs & Resource Efficiency Page:** Currently not working; under maintenance.
* **Free-Tier Limits:** Prone to cold starts, database limits, and rate limits.
* **Port Conflicts:** Local dev requires strictly ports `8000` & `5173` to be free.
* **AI Dependency:** Core AI features require Gemini and Mistral API keys to function.
