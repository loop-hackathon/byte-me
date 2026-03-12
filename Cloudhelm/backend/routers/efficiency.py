from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from backend.core.db import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.services.efficiency_service import EfficiencyService
from backend.services.cost_billing import cost_billing_service
from backend.services.health_service import health_service

router = APIRouter(prefix="/efficiency", tags=["efficiency"])
logger = logging.getLogger(__name__)

@router.post("/upload-grafana")
async def upload_grafana_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload Grafana CPU utilization CSV data (Stored in Cache)."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    content = await file.read()
    csv_text = content.decode('utf-8')
    
    success = EfficiencyService.store_csv_data(current_user.id, "grafana", csv_text)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process CSV data")
        
    return {"status": "success", "message": "Grafana data cached successfully"}

@router.post("/upload-gemini")
async def upload_gemini_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload Gemini cost trend CSV data (Stored in Cache)."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    content = await file.read()
    csv_text = content.decode('utf-8')
    
    success = EfficiencyService.store_csv_data(current_user.id, "gemini", csv_text)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process CSV data")
        
    return {"status": "success", "message": "Gemini data cached successfully"}

@router.get("/resources")
async def get_resource_efficiency(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Cost vs CPU Utilization analysis data."""
    try:
        # Fetch dynamic health metrics (Real-time Prometheus + DB)
        dynamic_metrics = []
        try:
            dynamic_metrics = health_service.get_health_summary(db, user_id=current_user.id)
        except Exception as e:
            logger.warning(f"Could not fetch dynamic health metrics: {e}")

        # Fetch actual costs from DB to combine with CSV data
        db_costs = []
        try:
            # Get cost by service for the current user
            costs = cost_billing_service.get_cost_by_service(db, current_user.id)
            db_costs = [{"service": c.service, "cost": c.amount} for c in costs]
        except Exception as e:
            logger.warning(f"Could not fetch DB costs: {e}")

        analysis = EfficiencyService.get_resource_efficiency(current_user.id, db_costs, dynamic_metrics)
        return analysis
    except Exception as e:
        logger.error(f"Error getting efficiency data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
