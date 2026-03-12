# CloudHelm Overview

## ✅ Working Features
* **Trivy Security Scanning:** Trivy is fully running — performs container vulnerability scanning and returns detailed diagnostics including severity levels, CVE IDs, descriptions, and links to advisories.
* **Incident Management:** AI-powered incident summaries, timeline tracking, and incident diagnostics powered by Trivy scan results.
* **SBOM (Software Bill of Materials):** Users can view SBOM details directly in the UI or download the full SBOM as a JSON file for offline analysis and compliance.
* **Tenant Isolation:** Robust user isolation and multi-tenancy support.
* **Application Health:** End-to-end performance and latency monitoring with Docker/K8s integration, including app health using Grafana, and services monitoring (now with Trace Services) in the App Health page.
* **Release Impact Analysis:** Deployment risk scoring, GitHub release correlation, and integrated vulnerability & SBOM data per release.
* **CloudHelm Assistant:** Mistral AI CLI coding assistant `/test`, `/lint`, `/run` inside the app.
* **Cloud Cost Management:** Comprehensive cloud spend tracking, AI-powered cost optimization recommendations, and detailed resource efficiency analysis. It takes the CSV files in the cost page to give results with an SLA report (downloadable with a single click).
* **LLM Integration:** Full LLM support for AI-driven insights and automated workflows across the platform.

## ⚠️ Known Issues & Limitations
* **Free-Tier Limits:** Prone to cold starts, database limits, and rate limits.
* **Port Conflicts:** Local dev requires strictly ports `8000` & `5173` to be free.
* **AI Dependency:** Core AI features require Gemini and Mistral API keys to function.
