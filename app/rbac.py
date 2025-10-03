# app/rbac.py
"""
Role-Based Access Control (RBAC) system for Jimini.
Controls access to admin endpoints based on user roles.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from fastapi import HTTPException, Request
import jwt
import os


class Role(Enum):
    """Standard user roles"""
    ADMIN = "ADMIN"
    REVIEWER = "REVIEWER" 
    SUPPORT = "SUPPORT"
    USER = "USER"


@dataclass
class User:
    """User representation with roles"""
    id: str
    username: str
    roles: List[Role]
    email: Optional[str] = None


class RBACManager:
    """RBAC manager for role-based endpoint protection"""
    
    def __init__(self, enabled: bool = False, jwt_secret: Optional[str] = None):
        self.enabled = enabled
        self.jwt_secret = jwt_secret or os.getenv('RBAC_JWT_SECRET', 'default-secret-change-in-prod')
        
        # Role hierarchies (higher roles include lower role permissions)
        self.role_hierarchy = {
            Role.ADMIN: [Role.ADMIN, Role.REVIEWER, Role.SUPPORT, Role.USER],
            Role.REVIEWER: [Role.REVIEWER, Role.SUPPORT, Role.USER], 
            Role.SUPPORT: [Role.SUPPORT, Role.USER],
            Role.USER: [Role.USER]
        }
    
    def extract_user_from_request(self, request: Request) -> Optional[User]:
        """
        Extract user information from request.
        Supports JWT tokens in Authorization header or API key mapping.
        """
        if not self.enabled:
            # If RBAC disabled, return admin user
            return User(id="system", username="system", roles=[Role.ADMIN])
        
        # Try JWT token first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                roles = [Role(r) for r in payload.get("roles", ["USER"])]
                return User(
                    id=payload.get("sub", "unknown"),
                    username=payload.get("username", payload.get("sub", "unknown")),
                    roles=roles,
                    email=payload.get("email")
                )
            except jwt.InvalidTokenError:
                return None
        
        # Fallback: API key to role mapping (simplified)
        api_key = request.headers.get("X-API-Key") or getattr(request, 'api_key', None)
        if api_key:
            # Simple mapping for demo - in production use proper user store
            api_key_roles = {
                "admin-key": [Role.ADMIN],
                "reviewer-key": [Role.REVIEWER],
                "support-key": [Role.SUPPORT]
            }
            
            if api_key in api_key_roles:
                return User(
                    id=f"apikey-{api_key[-4:]}",
                    username=f"apikey-user-{api_key[-4:]}",
                    roles=api_key_roles[api_key]
                )
        
        return None
    
    def has_role(self, user: Optional[User], required_role: Role) -> bool:
        """Check if user has required role (or higher in hierarchy)"""
        if not self.enabled:
            return True
        
        if not user:
            return False
        
        # Check if any of user's roles include the required role
        for user_role in user.roles:
            if required_role in self.role_hierarchy.get(user_role, []):
                return True
        
        return False
    
    def require_role(self, required_role: Role):
        """
        Decorator factory for protecting endpoints with role requirements.
        Usage: @rbac.require_role(Role.ADMIN)
        """
        def decorator(func):
            def wrapper(request: Request, *args, **kwargs):
                user = self.extract_user_from_request(request)
                
                if not self.has_role(user, required_role):
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "Insufficient permissions",
                            "required_role": required_role.value,
                            "user_roles": [r.value for r in user.roles] if user else [],
                            "rbac_enabled": self.enabled
                        }
                    )
                
                # Add user to request context for use in endpoint
                if hasattr(request, 'state'):
                    request.state.user = user
                
                return func(request, *args, **kwargs)
            
            return wrapper
        return decorator
    
    def check_access(self, request: Request, required_role: Role) -> Dict[str, Any]:
        """
        Check access and return detailed result for debugging.
        Used in health/debug endpoints.
        """
        user = self.extract_user_from_request(request)
        has_access = self.has_role(user, required_role)
        
        return {
            "rbac_enabled": self.enabled,
            "user": {
                "id": user.id if user else None,
                "username": user.username if user else None,
                "roles": [r.value for r in user.roles] if user else []
            } if user else None,
            "required_role": required_role.value,
            "has_access": has_access,
            "reason": "Access granted" if has_access else (
                "No user found" if not user else 
                f"User roles {[r.value for r in user.roles]} do not include {required_role.value}"
            )
        }
    
    def generate_token(self, user: User, expires_hours: int = 24) -> str:
        """Generate JWT token for user (for testing/admin use)"""
        import datetime
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "roles": [r.value for r in user.roles],
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_hours),
            "iat": datetime.datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def get_rbac_status(self) -> Dict[str, Any]:
        """Get RBAC system status"""
        return {
            "enabled": self.enabled,
            "jwt_configured": bool(self.jwt_secret and self.jwt_secret != 'default-secret-change-in-prod'),
            "supported_roles": [r.value for r in Role],
            "role_hierarchy": {
                role.value: [r.value for r in permissions]
                for role, permissions in self.role_hierarchy.items()
            }
        }


# Global RBAC instance
_rbac_instance = None


def get_rbac() -> RBACManager:
    """Get global RBAC instance"""
    global _rbac_instance
    if _rbac_instance is None:
        from config.loader import get_current_config
        config = get_current_config()
        _rbac_instance = RBACManager(enabled=config.security.rbac_enabled)
    return _rbac_instance


def reset_rbac():
    """Reset RBAC instance (for testing)"""
    global _rbac_instance
    _rbac_instance = None