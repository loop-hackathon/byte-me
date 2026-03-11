"""
Authentication router with GitHub and Google OAuth flows.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
import httpx

from backend.core.config import settings
from backend.core.db import get_db
from backend.core.security import create_access_token, get_current_user
from backend.models.user import User
from backend.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/github/login")
async def github_login():
    """Redirect to GitHub OAuth authorization page."""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=read:user user:email"
    )
    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle GitHub OAuth callback.
    Exchange code for access token, fetch user profile, and issue JWT.
    """
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for access token"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from GitHub"
            )
        
        # Fetch user profile
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user profile from GitHub"
            )
        
        user_data = user_response.json()
        
        # Fetch user emails
        email = user_data.get("email")
        if not email:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            if emails_response.status_code == 200:
                emails = emails_response.json()
                primary_email = next(
                    (e["email"] for e in emails if e.get("primary")),
                    None
                )
                email = primary_email
    
    # Upsert user in database
    provider_id = str(user_data["id"])
    user = db.query(User).filter(
        User.provider == "github",
        User.provider_id == provider_id
    ).first()
    
    if user:
        # Update existing user
        user.email = email
        user.name = user_data.get("name") or user_data.get("login")
        user.github_access_token = access_token  # Store the GitHub token
    else:
        # Create new user
        user = User(
            provider="github",
            provider_id=provider_id,
            email=email,
            name=user_data.get("name") or user_data.get("login"),
            github_access_token=access_token  # Store the GitHub token
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    # Create JWT token
    jwt_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.jwt_access_token_expires_minutes)
    )
    
    # Redirect to frontend dashboard with token
    redirect_url = f"{settings.frontend_origin}/dashboard?token={jwt_token}"
    response = RedirectResponse(url=redirect_url)
    
    # Also set as HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        max_age=settings.jwt_access_token_expires_minutes * 60,
        samesite="lax"
    )
    
    return response


@router.get("/google/login")
async def google_login():
    """Redirect to Google OAuth authorization page."""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    Exchange code for access token, fetch user profile, and issue JWT.
    """
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for access token"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from Google"
            )
        
        # Fetch user profile
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user profile from Google"
            )
        
        user_data = user_response.json()
    
    # Upsert user in database
    provider_id = user_data["id"]
    user = db.query(User).filter(
        User.provider == "google",
        User.provider_id == provider_id
    ).first()
    
    if user:
        # Update existing user
        user.email = user_data.get("email")
        user.name = user_data.get("name")
    else:
        # Create new user
        user = User(
            provider="google",
            provider_id=provider_id,
            email=user_data.get("email"),
            name=user_data.get("name")
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    # Create JWT token
    jwt_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.jwt_access_token_expires_minutes)
    )
    
    # Redirect to frontend dashboard with token
    redirect_url = f"{settings.frontend_origin}/dashboard?token={jwt_token}"
    response = RedirectResponse(url=redirect_url)
    
    # Also set as HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        max_age=settings.jwt_access_token_expires_minutes * 60,
        samesite="lax"
    )
    
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@router.post("/logout")
async def logout():
    """Logout user by clearing the access token cookie."""
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="access_token")
    return response
