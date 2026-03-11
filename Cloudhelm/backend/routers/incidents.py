"""
Incident router for CloudHelm API.
Provides endpoints for incident management and AI-powered summaries.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from uuid import uuid4
from datetime import datetime

from backend.core.db import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    GenerateSummaryRequest,
    GenerateSummaryResponse
)
from backend.services.incident_service import incident_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    service: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all incidents with optional filters.
    
    Query Parameters:
    - status: Filter by status (investigating, identified, monitoring, resolved)
    - severity: Filter by severity (low, medium, high, critical)
    - service: Filter by service name
    - limit: Maximum number of results (default: 100)
    """
    try:
        incidents = incident_service.list_incidents(
            db,
            status=status,
            severity=severity,
            service=service,
            limit=limit
        )
        return incidents
    except Exception as e:
        logger.error(f"Error listing incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get incident by ID"""
    incident = incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new incident.
    
    The incident will be created without an AI summary initially.
    Use the /incidents/{id}/generate-summary endpoint to generate one.
    """
    try:
        # Check if incident_id already exists
        existing = incident_service.get_incident_by_incident_id(db, incident_data.incident_id)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Incident with ID {incident_data.incident_id} already exists"
            )
        
        incident = incident_service.create_incident(db, incident_data)
        return incident
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing incident"""
    try:
        incident = incident_service.update_incident(db, incident_id, incident_data)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        return incident
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an incident"""
    try:
        success = incident_service.delete_incident(db, incident_id)
        if not success:
            raise HTTPException(status_code=404, detail="Incident not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{incident_id}/generate-summary", response_model=GenerateSummaryResponse)
def generate_incident_summary(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an AI-powered summary for an incident using Google Gemini.
    
    This endpoint:
    1. Retrieves the incident details
    2. Sends them to Gemini AI for analysis
    3. Saves the generated summary to the database
    4. Returns the summary
    
    The summary includes:
    - Executive Summary
    - Impact Assessment
    - Root Cause Hypothesis
    - Recommended Actions
    """
    try:
        incident = incident_service.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Generate AI summary
        summary = incident_service.generate_ai_summary(db, incident_id)
        
        if not summary:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate AI summary. Check if GEMINI_API_KEY is configured."
            )
        
        return GenerateSummaryResponse(
            incident_id=incident.incident_id,
            summary=summary,
            generated_at=datetime.utcnow().isoformat(),
            request_id=str(uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating incident summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/summary")
def get_incident_summary(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the AI-generated summary for an incident.
    
    Returns the cached summary if available, or null if not yet generated.
    Use POST /incidents/{id}/generate-summary to generate a new summary.
    """
    incident = incident_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return {
        "incident_id": incident.incident_id,
        "summary": incident.ai_summary,
        "generated_at": incident.summary_generated_at.isoformat() if incident.summary_generated_at else None
    }
