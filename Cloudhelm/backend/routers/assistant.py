"""
CloudHelm Assistant API endpoints using Mistral AI.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.security import get_current_user
from backend.models.user import User
from backend.services.mistral_service import mistral_service

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class AssistantRequest(BaseModel):
    """Request model for assistant queries"""
    repository_id: Optional[str] = None
    repository_name: Optional[str] = None
    query: str
    code_snippet: Optional[str] = None
    context_type: Optional[str] = "general"  # general, incident, security


class AssistantResponse(BaseModel):
    """Response model for assistant queries"""
    response: str
    repository_name: Optional[str] = None


class TaskDelegationRequest(BaseModel):
    """Request model for task delegation"""
    task_description: str
    agent_type: str
    repository_name: str
    context: Optional[dict] = None


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    description: str
    agent_type: str
    status: str
    repository: str
    result: Optional[str] = None
    error: Optional[str] = None


class InteractiveQuestionRequest(BaseModel):
    """Request model for interactive questions"""
    questions: list
    repository_name: str


@router.post("/delegate-task")
async def delegate_task(
    request: TaskDelegationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delegate a task to a specialized subagent"""
    try:
        task_id = await subagent_service.delegate_task(
            task_description=request.task_description,
            agent_type=request.agent_type,
            repository_name=request.repository_name,
            context=request.context
        )
        
        return {
            "task_id": task_id,
            "message": f"Task delegated to {request.agent_type} subagent",
            "status": "pending"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error delegating task: {str(e)}"
        )


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a delegated task"""
    try:
        status = subagent_service.get_task_status(task_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting task status: {str(e)}"
        )


@router.get("/active-tasks")
async def list_active_tasks(
    current_user: User = Depends(get_current_user)
):
    """List all active tasks"""
    try:
        active_tasks = subagent_service.list_active_tasks()
        completed_tasks = subagent_service.list_completed_tasks(10)
        
        return {
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing tasks: {str(e)}"
        )


@router.get("/available-agents")
async def get_available_agents(
    current_user: User = Depends(get_current_user)
):
    """Get list of available subagent types"""
    try:
        agents = subagent_service.get_available_agents()
        return {"agents": agents}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting available agents: {str(e)}"
        )


@router.post("/ask-questions")
async def ask_interactive_questions(
    request: InteractiveQuestionRequest,
    current_user: User = Depends(get_current_user)
):
    """Ask interactive questions to the user"""
    try:
        response_text = await mistral_service.ask_user_question(
            questions=request.questions,
            repository_name=request.repository_name
        )
        
        return AssistantResponse(
            response=response_text,
            repository_name=request.repository_name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error asking questions: {str(e)}"
        )


@router.post("/query", response_model=AssistantResponse)
async def query_assistant(
    request: AssistantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query the CloudHelm Assistant powered by Mistral AI.
    
    Supports different context types:
    - general: General code analysis and questions
    - incident: Incident analysis and solutions
    - security: Security vulnerability review
    """
    if not mistral_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Mistral AI service is not available. Please configure MISTRAL_API_KEY."
        )
    
    try:
        response_text = None
        
        if request.context_type == "incident":
            # Incident solution
            response_text = await mistral_service.suggest_incident_solution(
                repository_name=request.repository_name or "Unknown Repository",
                incident_description=request.query,
                error_logs=request.code_snippet
            )
        elif request.context_type == "security":
            # Security review
            response_text = await mistral_service.review_security(
                repository_name=request.repository_name or "Unknown Repository",
                code_snippet=request.code_snippet
            )
        else:
            # General code analysis
            response_text = await mistral_service.analyze_code(
                repository_name=request.repository_name or "Unknown Repository",
                code_snippet=request.code_snippet,
                question=request.query
            )
        
        if not response_text:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate response from Mistral AI"
            )
        
        return AssistantResponse(
            response=response_text,
            repository_name=request.repository_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing assistant query: {str(e)}"
        )


@router.get("/status")
async def get_assistant_status():
    """Check if the assistant service is available"""
    return {
        "enabled": mistral_service.enabled,
        "model": mistral_service.model if mistral_service.enabled else None,
        "service": "Mistral AI"
    }
