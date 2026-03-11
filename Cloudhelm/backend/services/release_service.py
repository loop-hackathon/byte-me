"""
Release service for business logic and risk analysis.
Adapted from Release-Impact-feature for CloudHelm.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from backend.models.release import Repository, Release, ReleaseAnomaly, ReleaseIncident
from backend.services.github_service import GitHubService
from backend.services import security_service as sec_svc

logger = logging.getLogger(__name__)


class ReleaseService:
    """Service for release operations and risk analysis"""
    
    @staticmethod
    def create_repository(db: Session, repo_data: dict, user_id: int) -> Repository:
        """Create a new repository in database"""
        # Check if repository already exists
        existing = db.query(Repository).filter(
            Repository.full_name == repo_data["full_name"],
            Repository.user_id == user_id
        ).first()
        
        if existing:
            # Update existing repository
            for key, value in repo_data.items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new repository
        repo = Repository(**repo_data, user_id=user_id)
        db.add(repo)
        db.commit()
        db.refresh(repo)
        return repo
    
    @staticmethod
    def get_repository(db: Session, repo_id: str) -> Optional[Repository]:
        """Get repository by ID"""
        return db.query(Repository).filter(Repository.id == repo_id).first()
    
    @staticmethod
    def get_repository_by_name(db: Session, full_name: str) -> Optional[Repository]:
        """Get repository by full name (owner/repo)"""
        return db.query(Repository).filter(Repository.full_name == full_name).first()
    
    @staticmethod
    def list_repositories(db: Session, user_id: int) -> List[Repository]:
        """List all repositories for a user"""
        return db.query(Repository).filter(
            Repository.user_id == user_id
        ).order_by(desc(Repository.last_deployment)).all()
    
    @staticmethod
    def update_repository_sync_status(
        db: Session, 
        repo_id: str, 
        is_syncing: bool,
        last_sync: Optional[datetime] = None
    ):
        """Update repository sync status"""
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if repo:
            repo.is_syncing = is_syncing
            if last_sync:
                repo.last_sync = last_sync
            db.commit()
    
    @staticmethod
    def create_release(db: Session, release_data: dict) -> Release:
        """Create a new release"""
        # Check if release already exists (by workflow_run_id)
        if release_data.get("workflow_run_id"):
            existing = db.query(Release).filter(
                Release.workflow_run_id == release_data["workflow_run_id"]
            ).first()
            
            if existing:
                logger.info(f"Release already exists: {existing.id}")
                return existing
        
        # Calculate risk score
        release_data["risk_score"] = ReleaseService.calculate_risk_score(release_data)
        release_data["risk_level"] = ReleaseService.get_risk_level(release_data["risk_score"])
        
        release = Release(**release_data)
        db.add(release)
        db.commit()
        db.refresh(release)
        
        # Update repository last_deployment
        repo = db.query(Repository).filter(Repository.id == release.repo_id).first()
        if repo:
            if not repo.last_deployment or release.deployed_at > repo.last_deployment:
                repo.last_deployment = release.deployed_at
                db.commit()
        
        return release
    
    @staticmethod
    def get_release(db: Session, release_id: str) -> Optional[Release]:
        """Get release by ID"""
        return db.query(Release).filter(Release.id == release_id).first()
    
    @staticmethod
    def list_releases(
        db: Session,
        repo_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50
    ) -> List[Release]:
        """List releases, optionally filtered by repository and risk level"""
        query = db.query(Release)
        
        if repo_id:
            query = query.filter(Release.repo_id == repo_id)
        
        if risk_level:
            query = query.filter(Release.risk_level == risk_level)
        
        return query.order_by(desc(Release.deployed_at)).limit(limit).all()
    
    @staticmethod
    def calculate_risk_score(release_data: dict, anomalies: List = None, incidents: List = None) -> float:
        """
        Calculate risk score for a release based on:
        - Deployment status
        - Deployment duration
        - Number of anomalies
        - Number of incidents
        - Cost delta
        
        Score range: 0-100
        """
        import random
        
        score = 0.0
        
        # Failed deployments are risky (70 points)
        if release_data.get("status") == "failed":
            score += 70
        
        # Long deployment times might indicate issues (30 points max)
        duration = release_data.get("deployment_duration", 0)
        if duration and duration > 300:  # More than 5 minutes
            score += 20
        if duration and duration > 600:  # More than 10 minutes
            score += 10
        
        # Anomalies contribute to risk (30 points max)
        if anomalies:
            anomaly_score = min(len(anomalies) * 5, 30)
            score += anomaly_score
        
        # Incidents contribute to risk (30 points max)
        if incidents:
            incident_score = min(len(incidents) * 10, 30)
            score += incident_score
        
        # Add some variance for demo purposes (0-20 points)
        # This simulates various factors like code complexity, test coverage, etc.
        score += random.uniform(0, 20)
        
        return min(score, 100.0)
    
    @staticmethod
    def get_risk_level(score: float) -> str:
        """
        Get risk level from score
        - Healthy: 0-30
        - Suspect: 31-69
        - Risky: 70-100
        """
        if score < 30:
            return "Healthy"
        elif score < 70:
            return "Suspect"
        else:
            return "Risky"

    
    @staticmethod
    def correlate_anomalies(
        db: Session,
        release_id: str,
        time_window_minutes: int = 60
    ) -> List[ReleaseAnomaly]:
        """
        Find anomalies that occurred within time window of release
        """
        release = db.query(Release).filter(Release.id == release_id).first()
        if not release:
            return []
        
        # Define time window
        window_start = release.deployed_at - timedelta(minutes=time_window_minutes)
        window_end = release.deployed_at + timedelta(minutes=time_window_minutes)
        
        # Query anomalies within window
        anomalies = db.query(ReleaseAnomaly).filter(
            ReleaseAnomaly.release_id == release_id,
            ReleaseAnomaly.timestamp >= window_start,
            ReleaseAnomaly.timestamp <= window_end
        ).all()
        
        return anomalies
    
    @staticmethod
    def correlate_incidents(
        db: Session,
        release_id: str,
        time_window_minutes: int = 120
    ) -> List[Dict]:
        """
        Find incidents that occurred within time window of release
        Returns list of incidents with correlation scores
        """
        release = db.query(Release).filter(Release.id == release_id).first()
        if not release:
            return []
        
        # Define time window
        window_start = release.deployed_at - timedelta(minutes=time_window_minutes)
        window_end = release.deployed_at + timedelta(minutes=time_window_minutes)
        
        # Query release incidents within window
        release_incidents = db.query(ReleaseIncident).filter(
            ReleaseIncident.release_id == release_id
        ).all()
        
        # For now, return the incidents with their correlation scores
        # In a full implementation, you'd query the Incident table and calculate correlation
        incidents = []
        for ri in release_incidents:
            incidents.append({
                "incident_id": ri.incident_id,
                "correlation_score": ri.correlation_score,
                "release_id": release_id
            })
        
        return incidents
    
    @staticmethod
    def get_release_impact(db: Session, release_id: str) -> Optional[Dict]:
        """
        Get comprehensive impact analysis for a release
        
        Returns:
        - Risk score and level
        - Detected anomalies
        - Related incidents
        - Cost impact
        - Before/after metrics
        """
        release = db.query(Release).filter(Release.id == release_id).first()
        if not release:
            return None
        
        # Get anomalies for this release
        anomalies = ReleaseService.correlate_anomalies(db, release_id)
        
        # Get incidents for this release
        incidents = ReleaseService.correlate_incidents(db, release_id)
        
        # Calculate anomaly counts by type
        anomaly_count = {
            "total": len(anomalies),
            "metric": len([a for a in anomalies if a.anomaly_type == "metric"]),
            "cost": len([a for a in anomalies if a.anomaly_type == "cost"]),
        }
        
        # Calculate cost delta
        cost_anomalies = [a for a in anomalies if a.anomaly_type == "cost"]
        cost_delta = {
            "amount": cost_anomalies[0].value - cost_anomalies[0].expected_value if cost_anomalies else 0,
            "percentage": cost_anomalies[0].deviation if cost_anomalies else 0,
        }

        # ------------------------------------------------------------------
        # Security scan (best-effort — never raises)
        # ------------------------------------------------------------------
        repo = db.query(Repository).filter(Repository.id == release.repo_id).first()
        repo_full_name = repo.full_name if repo else None

        security_impact: dict = {
            "risk_score": 0.0,
            "security_metrics": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "unknown": 0,
            },
            "scan_status": "not_run",
        }

        if repo_full_name:
            logger.info(
                "Running Trivy scan for release %s on repo %s (ref=%s)",
                release_id, repo_full_name, release.commit,
            )
            scan_result = sec_svc.scan_repository(
                repo_full_name=repo_full_name,
                token=None,          # TODO: pass user's GitHub token for private repos
                ref=release.commit,
            )

            if scan_result is not None:
                security_impact = {
                    "risk_score": scan_result["risk_score"],
                    "security_metrics": scan_result["security_metrics"],
                    "scan_status": "success",
                }
                # Blend: 60% existing risk score + 40% security score
                blended_score = (
                    0.6 * release.risk_score
                    + 0.4 * scan_result["risk_score"]
                )
                blended_risk_score = min(blended_score, 100.0)
                blended_risk_level = ReleaseService.get_risk_level(blended_risk_score)
                logger.info(
                    "Blended risk score: %.1f → %s",
                    blended_risk_score, blended_risk_level,
                )
            else:
                security_impact["scan_status"] = "failed"
                blended_risk_score = release.risk_score
                blended_risk_level = release.risk_level
        else:
            security_impact["scan_status"] = "skipped"
            blended_risk_score = release.risk_score
            blended_risk_level = release.risk_level
        
        return {
            "release_id": release_id,
            "risk_score": blended_risk_score,
            "risk_level": blended_risk_level,
            "anomaly_count": anomaly_count,
            "incident_count": len(incidents),
            "cost_delta": cost_delta,
            "anomalies": [
                {
                    "id": str(a.id),
                    "metric_name": a.metric_name,
                    "timestamp": a.timestamp.isoformat(),
                    "severity": a.severity,
                    "value": a.value,
                    "expected_value": a.expected_value,
                    "deviation": a.deviation,
                    "type": a.anomaly_type
                }
                for a in anomalies
            ],
            "incidents": incidents,
            "metrics_before_after": [],  # TODO: Implement metrics comparison
            "security": security_impact,
        }
    
    @staticmethod
    def sync_repository(
        db: Session,
        owner: str,
        repo: str,
        github_token: str,
        user_id: int
    ) -> Repository:
        """
        Sync repository and releases from GitHub
        """
        github_service = GitHubService(github_token)
        
        # Get repository info from GitHub
        repo_info = github_service.get_repository(owner, repo)
        
        # Create or update repository in database
        db_repo = ReleaseService.create_repository(db, repo_info, user_id)
        
        # Mark as syncing
        ReleaseService.update_repository_sync_status(db, str(db_repo.id), True)
        
        try:
            # Get releases from GitHub (workflow runs)
            releases = github_service.get_workflow_runs(owner, repo)
            
            logger.info(f"Fetched {len(releases)} releases from GitHub")
            
            # Store releases in database
            for release_data in releases:
                release_data["repo_id"] = str(db_repo.id)
                ReleaseService.create_release(db, release_data)
            
            # Mark sync as complete
            ReleaseService.update_repository_sync_status(
                db, 
                str(db_repo.id), 
                False, 
                datetime.utcnow()
            )
            
            logger.info(f"Successfully synced {owner}/{repo}")
            return db_repo
            
        except Exception as e:
            logger.error(f"Error syncing repository: {e}")
            ReleaseService.update_repository_sync_status(db, str(db_repo.id), False)
            raise


# Singleton instance
release_service = ReleaseService()
