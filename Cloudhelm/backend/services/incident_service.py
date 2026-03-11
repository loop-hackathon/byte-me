"""
Incident service for managing incidents and generating AI summaries.
"""
import logging
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.cost import Incident
from backend.schemas.incident import IncidentCreate, IncidentUpdate
from backend.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class IncidentService:
    """Service for managing incidents"""
    
    def __init__(self):
        """Initialize incident service with Gemini AI"""
        self.gemini_service = GeminiService()
    
    def list_incidents(
        self,
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 100
    ) -> List[Incident]:
        """
        List incidents with optional filters.
        
        Args:
            db: Database session
            status: Filter by status
            severity: Filter by severity
            service: Filter by service
            limit: Maximum number of results
            
        Returns:
            List of incidents
        """
        query = db.query(Incident)
        
        if status:
            query = query.filter(Incident.status == status)
        if severity:
            query = query.filter(Incident.severity == severity)
        if service:
            query = query.filter(Incident.service == service)
        
        incidents = query.order_by(desc(Incident.created_at)).limit(limit).all()
        return incidents
    
    def get_incident(self, db: Session, incident_id: int) -> Optional[Incident]:
        """Get incident by ID"""
        return db.query(Incident).filter(Incident.id == incident_id).first()
    
    def get_incident_by_incident_id(self, db: Session, incident_id: str) -> Optional[Incident]:
        """Get incident by incident_id string (e.g., INC-2024-001)"""
        return db.query(Incident).filter(Incident.incident_id == incident_id).first()
    
    def create_incident(self, db: Session, incident_data: IncidentCreate) -> Incident:
        """
        Create a new incident.
        
        Args:
            db: Database session
            incident_data: Incident creation data
            
        Returns:
            Created incident
        """
        incident = Incident(
            incident_id=incident_data.incident_id,
            title=incident_data.title,
            description=incident_data.description,
            service=incident_data.service,
            env=incident_data.env,
            team=incident_data.team,
            status=incident_data.status,
            severity=incident_data.severity,
            anomalies=incident_data.anomalies,
            recent_releases=incident_data.recent_releases,
            metrics_summary=incident_data.metrics_summary,
            cost_changes=incident_data.cost_changes,
            created_at=date.today()
        )
        
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        logger.info(f"Created incident {incident.incident_id}")
        return incident
    
    def update_incident(
        self,
        db: Session,
        incident_id: int,
        incident_data: IncidentUpdate
    ) -> Optional[Incident]:
        """
        Update an existing incident.
        
        Args:
            db: Database session
            incident_id: Incident ID
            incident_data: Update data
            
        Returns:
            Updated incident or None if not found
        """
        incident = self.get_incident(db, incident_id)
        if not incident:
            return None
        
        # Update fields if provided
        update_data = incident_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(incident, field, value)
        
        db.commit()
        db.refresh(incident)
        
        logger.info(f"Updated incident {incident.incident_id}")
        return incident
    
    def delete_incident(self, db: Session, incident_id: int) -> bool:
        """
        Delete an incident.
        
        Args:
            db: Database session
            incident_id: Incident ID
            
        Returns:
            True if deleted, False if not found
        """
        incident = self.get_incident(db, incident_id)
        if not incident:
            return False
        
        db.delete(incident)
        db.commit()
        
        logger.info(f"Deleted incident {incident.incident_id}")
        return True
    
    def generate_ai_summary(self, db: Session, incident_id: int) -> Optional[str]:
        """
        Generate AI summary for an incident.
        
        Args:
            db: Database session
            incident_id: Incident ID
            
        Returns:
            Generated summary or None if generation fails
        """
        incident = self.get_incident(db, incident_id)
        if not incident:
            logger.error(f"Incident {incident_id} not found")
            return None
        
        # Generate summary using Gemini
        summary = self.gemini_service.generate_incident_summary(
            incident_id=incident.incident_id,
            service_name=incident.service or "Unknown",
            environment=incident.env or "Unknown",
            start_time=incident.created_at.isoformat(),
            status=incident.status,
            anomalies=incident.anomalies or "No anomalies recorded",
            recent_releases=incident.recent_releases or "No recent releases recorded",
            metrics_summary=incident.metrics_summary or "No metrics available",
            cost_changes=incident.cost_changes
        )
        
        if summary:
            # Save summary to database
            incident.ai_summary = summary
            incident.summary_generated_at = date.today()
            db.commit()
            db.refresh(incident)
            
            logger.info(f"Generated AI summary for incident {incident.incident_id}")
        
        return summary


# Global instance
incident_service = IncidentService()
