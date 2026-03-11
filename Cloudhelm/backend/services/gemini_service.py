"""
Gemini AI service for generating incident summaries.
Adapted from T-HACK AI Copilot Service.
Uses REST API directly to avoid dependency conflicts.
"""
import logging
import json
from typing import Optional
import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI via REST API"""
    
    def __init__(self):
        """Initialize Gemini service with API key from settings"""
        self.api_key = settings.gemini_api_key
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment. AI summaries will not be available.")
            self.enabled = False
            return
        
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        self.enabled = True
        logger.info("Gemini AI service initialized successfully (REST API - Model: gemini-2.0-flash-exp)")
    
    def generate_incident_summary(
        self,
        incident_id: str,
        service_name: str,
        environment: str,
        start_time: str,
        status: str,
        anomalies: str,
        recent_releases: str,
        metrics_summary: str,
        cost_changes: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate an AI-powered incident summary.
        
        Args:
            incident_id: Unique incident identifier
            service_name: Name of the affected service
            environment: Deployment environment
            start_time: When the incident started (ISO format)
            status: Current incident status
            anomalies: Description of detected anomalies
            recent_releases: Recent deployments that may be related
            metrics_summary: Summary of relevant metrics
            cost_changes: Optional cost impact information
            
        Returns:
            Markdown-formatted incident summary or None if generation fails
        """
        if not self.enabled:
            logger.warning("Gemini AI is not enabled. Cannot generate summary.")
            return None
        
        try:
            # Build the prompt
            prompt = self._build_prompt(
                incident_id=incident_id,
                service_name=service_name,
                environment=environment,
                start_time=start_time,
                status=status,
                anomalies=anomalies,
                recent_releases=recent_releases,
                metrics_summary=metrics_summary,
                cost_changes=cost_changes
            )
            
            # Call Gemini REST API
            url = f"{self.api_url}?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 800,
                }
            }
            
            # Use httpx for async HTTP requests
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract text from response
                if not data.get("candidates"):
                    logger.error("Gemini returned no candidates")
                    return None
                
                candidate = data["candidates"][0]
                if not candidate.get("content", {}).get("parts"):
                    logger.error("Gemini returned no content parts")
                    return None
                
                text = candidate["content"]["parts"][0].get("text", "")
                
                if not text:
                    logger.error("Gemini returned empty text")
                    return None
                
                logger.info(f"Successfully generated AI summary for incident {incident_id}")
                return text
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Gemini API: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return None
    
    def _build_prompt(
        self,
        incident_id: str,
        service_name: str,
        environment: str,
        start_time: str,
        status: str,
        anomalies: str,
        recent_releases: str,
        metrics_summary: str,
        cost_changes: Optional[str] = None
    ) -> str:
        """Build the prompt for Gemini AI"""
        
        cost_section = ""
        if cost_changes:
            cost_section = f"\n**Cost Changes:**\n{cost_changes}\n"
        
        prompt = f"""You are an SRE copilot assistant helping engineers understand and respond to production incidents. Your role is to analyze incident data and provide clear, actionable insights that help teams quickly understand the situation and take appropriate action.

Generate a concise, actionable incident summary based on the following information:

**Incident Details:**
- Incident ID: {incident_id}
- Service: {service_name}
- Environment: {environment}
- Start Time: {start_time}
- Current Status: {status}

**Anomalies Detected:**
{anomalies}

**Recent Releases:**
{recent_releases}

**Metrics Summary:**
{metrics_summary}
{cost_section}
---

**Instructions:**

Generate a structured summary with exactly these four sections. Use markdown formatting throughout.

## Executive Summary
Provide 2-3 sentences that describe:
- What is happening (the primary symptom or failure mode)
- When it started and current duration
- The immediate business or user impact

Be direct and avoid speculation. Focus on observable facts.

## Impact Assessment
Use bullet points to describe:
- Scope of impact (which users, regions, or features are affected)
- Severity level based on the metrics and anomalies
- Any cascading effects on dependent services
- Current status of mitigation efforts if mentioned

Quantify impact where possible using the metrics provided.

## Root Cause Hypothesis
Based on the anomalies, recent releases, and metrics, provide:
- The most likely root cause(s) in order of probability
- Supporting evidence from the data provided
- Any correlations between releases and incident timing
- Alternative hypotheses if the primary cause is uncertain

Be analytical but acknowledge uncertainty where it exists.

## Recommended Actions
Provide a prioritized list of 3-5 specific next steps:
1. Immediate actions to mitigate impact
2. Diagnostic steps to confirm root cause
3. Remediation steps if root cause is clear
4. Communication or escalation needs
5. Prevention measures for future consideration

Each action should be concrete and actionable, not generic advice.

---

**Style Guidelines:**
- Use technical language appropriate for SRE teams
- Be concise but thorough - aim for clarity over brevity
- Use bullet points and numbered lists for readability
- Include specific metrics, timestamps, or service names when relevant
- Maintain a calm, professional tone
- Avoid speculation presented as fact - use phrases like "likely", "suggests", "indicates" when inferring
- Do not include placeholder text like [insert details] - work with the information provided
"""
        
        return prompt
