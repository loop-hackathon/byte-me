"""
Release and repository routers for CloudHelm.
Adapted from Release-Impact-feature.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.core.db import get_db
from backend.core.security import get_current_user
from backend.core.config import settings
from backend.models.user import User
from backend.schemas.release import (
    RepositoryResponse, 
    ReleaseResponse, 
    ReleaseImpactResponse,
    SyncRequest
)
from backend.services.release_service import release_service

logger = logging.getLogger(__name__)

# Repositories Router
repos_router = APIRouter(prefix="/repos", tags=["repositories"])


@repos_router.get("", response_model=List[RepositoryResponse])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all repositories for the authenticated user"""
    try:
        repos = release_service.list_repositories(db, current_user.id)
        return repos
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@repos_router.get("/github/user-repos")
async def get_user_github_repos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all repositories from GitHub and save to database"""
    try:
        from github import Github
        
        # Use the GitHub token from the logged-in user
        token = current_user.github_access_token
        
        if not token:
            logger.error(f"User {current_user.id} has no GitHub token stored")
            raise HTTPException(
                status_code=401,
                detail="Please login with GitHub to sync repositories. Your account doesn't have a GitHub token."
            )
        
        logger.info(f"Attempting to connect to GitHub for user {current_user.id}")
        
        # Connect to GitHub
        g = Github(token)
        user = g.get_user()
        
        logger.info(f"Successfully connected to GitHub as {user.login}")
        
        repos_list = []
        
        # Get all user repositories
        for repo in user.get_repos():
            # Prepare repo data for database
            repo_data = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "",
                "language": repo.language or "Unknown",
                "stars": repo.stargazers_count,
                "owner": repo.owner.login,
                "github_id": repo.id,
            }
            
            # Save to database (or update if exists)
            db_repo = release_service.create_repository(db, repo_data, current_user.id)
            
            # Return database version (with proper UUID id)
            repos_list.append({
                "id": str(db_repo.id),
                "name": db_repo.name,
                "full_name": db_repo.full_name,
                "description": db_repo.description,
                "language": db_repo.language,
                "stars": db_repo.stars,
                "owner": db_repo.owner,
                "last_deployment": db_repo.last_deployment.isoformat() if db_repo.last_deployment else None,
                "is_syncing": db_repo.is_syncing,
                "last_sync": db_repo.last_sync.isoformat() if db_repo.last_sync else None
            })
        
        logger.info(f"Fetched and saved {len(repos_list)} repositories from GitHub")
        return repos_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GitHub repos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch repositories: {str(e)}")


@repos_router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(
    repo_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get repository by ID"""
    repo = release_service.get_repository(db, repo_id)
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@repos_router.post("/sync")
def sync_repository(
    sync_request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync repository from GitHub"""
    try:
        # Use the GitHub token from the logged-in user
        token = current_user.github_access_token
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Please login with GitHub to sync repositories."
            )
        
        # Sync repository
        repo = release_service.sync_repository(
            db,
            sync_request.owner,
            sync_request.repo,
            token,
            current_user.id
        )
        
        return {
            "message": "Repository synced successfully",
            "repository": {
                "id": str(repo.id),
                "full_name": repo.full_name,
                "releases_count": len(repo.releases)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@repos_router.get("/{repo_id}/releases")
def get_repository_releases(
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all releases for a repository"""
    try:
        # Verify repository exists
        repo = release_service.get_repository(db, repo_id)
        if not repo or repo.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Get releases
        releases = release_service.list_releases(db, repo_id=repo_id)
        
        return releases
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting repository releases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@repos_router.post("/{repo_id}/sync-releases")
def sync_repository_releases(
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync releases/deployments for a specific repository from GitHub"""
    try:
        # Get repository
        repo = release_service.get_repository(db, repo_id)
        if not repo or repo.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Use the GitHub token from the logged-in user
        token = current_user.github_access_token
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Please login with GitHub to sync releases."
            )
        
        logger.info(f"Syncing releases for repository {repo.full_name}")
        
        # Parse owner and repo name
        owner, repo_name = repo.full_name.split('/')
        
        # Use release service to sync
        from backend.services.github_service import GitHubService
        github_service = GitHubService(token)
        
        # Try to get workflow runs first (most common for CI/CD)
        releases = github_service.get_workflow_runs(owner, repo_name, limit=50)
        
        # If no workflow runs, try release tags
        if not releases:
            logger.info(f"No workflow runs found, trying release tags for {repo.full_name}")
            releases = github_service.get_release_tags(owner, repo_name, limit=20)
        
        # If still no releases, create a synthetic one from the latest commit
        if not releases:
            logger.info(f"No releases or tags found, creating synthetic release from latest commit")
            try:
                repo_obj = github_service.client.get_repo(f"{owner}/{repo_name}")
                default_branch = repo_obj.default_branch
                latest_commit = repo_obj.get_branch(default_branch).commit
                
                releases = [{
                    "service": repo_name,
                    "version": "latest",
                    "commit": latest_commit.sha[:8],
                    "branch": default_branch,
                    "deployed_at": latest_commit.commit.author.date,
                    "status": "success",
                    "triggered_by": latest_commit.author.login if latest_commit.author else None,
                }]
            except Exception as e:
                logger.warning(f"Could not create synthetic release: {e}")
        
        logger.info(f"Found {len(releases)} releases for {repo.full_name}")
        
        # Save releases to database
        saved_count = 0
        for release_data in releases:
            release_data["repo_id"] = str(repo.id)
            try:
                release_service.create_release(db, release_data)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Could not save release: {e}")
                continue
        
        return {
            "message": f"Successfully synced {saved_count} releases",
            "repository": {
                "id": str(repo.id),
                "full_name": repo.full_name,
                "releases_count": saved_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing repository releases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Releases Router
releases_router = APIRouter(prefix="/releases", tags=["releases"])


@releases_router.get("", response_model=List[ReleaseResponse])
def list_releases(
    repo_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all releases
    
    Optionally filter by repository ID and risk level
    """
    try:
        # If repo_id is provided, verify ownership
        if repo_id:
            repo = release_service.get_repository(db, repo_id)
            if not repo or repo.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="Repository not found")
        
        # TODO: In a real app, list_releases would also take user_id or list of repo_ids
        releases = release_service.list_releases(
            db, 
            repo_id=repo_id, 
            risk_level=risk_level,
            limit=limit
        )
        
        # If no repo_id was provided, we must filter results by user's repositories
        if not repo_id:
            user_repo_ids = [r.id for r in release_service.list_repositories(db, current_user.id)]
            releases = [r for r in releases if r.repo_id in user_repo_ids]
            
        return releases
    except Exception as e:
        logger.error(f"Error listing releases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@releases_router.get("/{release_id}", response_model=ReleaseResponse)
def get_release(
    release_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get release by ID
    
    Returns detailed information about a specific release
    """
    release = release_service.get_release(db, release_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
        
    # Verify ownership via repository
    repo = release_service.get_repository(db, release.repo_id)
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Release not found")
        
    return release


@releases_router.get("/{release_id}/impact")
def get_release_impact(
    release_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get release impact analysis
    
    Returns comprehensive impact analysis including:
    - Risk score and level
    - Detected anomalies
    - Related incidents
    - Cost impact
    - Before/after metrics
    """
    try:
        release = release_service.get_release(db, release_id)
        if not release:
            raise HTTPException(status_code=404, detail="Release not found")
            
        # Verify ownership via repository
        repo = release_service.get_repository(db, release.repo_id)
        if not repo or repo.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Release not found")

        impact = release_service.get_release_impact(db, release_id)
        if not impact:
            raise HTTPException(status_code=404, detail="Release not found")
        
        return impact
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting release impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))
