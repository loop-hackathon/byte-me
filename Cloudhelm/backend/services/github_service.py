"""
GitHub API service for fetching repository and deployment data.
Adapted from Release-Impact-feature for CloudHelm.
"""
from github import Github, GithubException
from typing import List, Dict, Optional
from datetime import datetime
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with token"""
        # Use provided token or fall back to settings
        self.token = token or settings.github_client_secret  # Using OAuth secret as token
        if not self.token:
            raise ValueError("GitHub token is required")
        
        self.client = Github(self.token)
        
    def get_repository(self, owner: str, repo: str) -> Dict:
        """Get repository information from GitHub"""
        try:
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            
            return {
                "name": repo_obj.name,
                "full_name": repo_obj.full_name,
                "description": repo_obj.description or "",
                "language": repo_obj.language or "Unknown",
                "stars": repo_obj.stargazers_count,
                "owner": repo_obj.owner.login,
                "github_id": repo_obj.id,
            }
        except GithubException as e:
            logger.error(f"Error fetching repository {owner}/{repo}: {e}")
            raise
    
    def get_workflow_runs(
        self, 
        owner: str, 
        repo: str, 
        branch: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get workflow runs (deployments) from GitHub Actions
        
        This fetches the workflow run history which represents deployments
        """
        try:
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            
            # Try to get default branch if not specified
            if not branch:
                branch = repo_obj.default_branch
                logger.info(f"Using default branch: {branch}")
            
            # Try with branch filter first
            try:
                workflows = repo_obj.get_workflow_runs(
                    branch=branch,
                    event="push"
                )
            except GithubException as e:
                # If branch filter fails, try without it
                logger.warning(f"Branch filter failed, trying without branch: {e}")
                workflows = repo_obj.get_workflow_runs(event="push")
            
            releases = []
            count = 0
            
            for run in workflows:
                if count >= limit:
                    break
                
                # Only process completed runs
                if run.status != "completed":
                    continue
                
                # Extract deployment information
                release_data = {
                    "service": repo,
                    "version": self._extract_version(run),
                    "commit": run.head_sha[:8],
                    "branch": run.head_branch,
                    "deployed_at": run.created_at,
                    "status": "success" if run.conclusion == "success" else "failed",
                    "deployment_duration": self._calculate_duration(run),
                    "triggered_by": run.actor.login if run.actor else None,
                    "workflow_run_id": str(run.id),
                    "github_run_number": run.run_number,
                }
                
                releases.append(release_data)
                count += 1
            
            logger.info(f"Found {len(releases)} workflow runs for {owner}/{repo}")
            return releases
            
        except GithubException as e:
            logger.error(f"Error fetching workflow runs for {owner}/{repo}: {e}")
            # Return empty list instead of raising to allow fallback to tags
            return []
    
    def get_release_tags(self, owner: str, repo: str, limit: int = 20) -> List[Dict]:
        """
        Get releases/tags from GitHub
        
        Alternative method to get version information
        """
        try:
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            releases = repo_obj.get_releases()
            
            release_list = []
            count = 0
            
            for release in releases:
                if count >= limit:
                    break
                
                # Get the commit for this release
                try:
                    commit = repo_obj.get_commit(release.tag_name)
                    
                    release_data = {
                        "service": repo,
                        "version": release.tag_name.lstrip('v'),
                        "commit": commit.sha[:8],
                        "branch": release.target_commitish or "main",
                        "deployed_at": release.published_at or release.created_at,
                        "status": "success",
                        "triggered_by": release.author.login if release.author else None,
                    }
                    
                    release_list.append(release_data)
                    count += 1
                    
                except Exception as e:
                    logger.warning(f"Could not process release {release.tag_name}: {e}")
                    continue
            
            logger.info(f"Found {len(release_list)} releases for {owner}/{repo}")
            return release_list
            
        except GithubException as e:
            logger.error(f"Error fetching releases for {owner}/{repo}: {e}")
            return []
    
    def _extract_version(self, run) -> str:
        """Extract version from workflow run"""
        # Try to extract version from tag or branch name
        head_branch = run.head_branch
        
        # Check if it's a version tag
        if head_branch and head_branch.startswith('v'):
            return head_branch.lstrip('v')
        
        # Otherwise, use run number as version
        return f"build-{run.run_number}"
    
    def _calculate_duration(self, run) -> Optional[int]:
        """Calculate workflow duration in seconds"""
        if run.updated_at and run.created_at:
            delta = run.updated_at - run.created_at
            return int(delta.total_seconds())
        return None
    
    def test_connection(self) -> bool:
        """Test GitHub API connection"""
        try:
            user = self.client.get_user()
            logger.info(f"Connected to GitHub as: {user.login}")
            return True
        except GithubException as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False


# Helper function to get GitHub service instance
def get_github_service(token: Optional[str] = None) -> GitHubService:
    return GitHubService(token)
