"""
Advanced Security and Authentication System for OmniDesk AI
Provides JWT/OAuth2 authentication, role-based access control, rate limiting,
and comprehensive security features for production deployment.
"""

from fastapi import Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
import secrets
import logging
import hashlib
import time
import asyncio
from dataclasses import dataclass
from enum import Enum
import ipaddress
import re
import uuid
from functools import wraps

# Redis for session management and rate limiting
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Security configuration
@dataclass
class SecurityConfig:
    """Security configuration settings"""
    # JWT settings
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Password policy
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special: bool = True
    
    # Rate limiting
    default_rate_limit: int = 100  # requests per minute
    auth_rate_limit: int = 5      # auth attempts per minute
    
    # Security headers
    enable_security_headers: bool = True
    cors_origins: List[str] = None
    
    # Session management
    max_concurrent_sessions: int = 3
    session_timeout_minutes: int = 60

# User roles and permissions
class UserRole(str, Enum):
    """User roles with hierarchical permissions"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin" 
    MANAGER = "manager"
    AGENT = "agent"
    USER = "user"

class Permission(str, Enum):
    """System permissions"""
    # Ticket permissions
    CREATE_TICKET = "create_ticket"
    READ_TICKET = "read_ticket"
    UPDATE_TICKET = "update_ticket"
    DELETE_TICKET = "delete_ticket"
    ASSIGN_TICKET = "assign_ticket"
    
    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Analytics and reporting
    VIEW_ANALYTICS = "view_analytics"
    VIEW_REPORTS = "view_reports"
    
    # System administration
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    CONFIGURE_AI = "configure_ai"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: list(Permission),  # All permissions
    UserRole.ADMIN: [
        Permission.CREATE_TICKET, Permission.READ_TICKET, Permission.UPDATE_TICKET,
        Permission.ASSIGN_TICKET, Permission.CREATE_USER, Permission.READ_USER,
        Permission.UPDATE_USER, Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS,
        Permission.VIEW_LOGS
    ],
    UserRole.MANAGER: [
        Permission.READ_TICKET, Permission.UPDATE_TICKET, Permission.ASSIGN_TICKET,
        Permission.READ_USER, Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS
    ],
    UserRole.AGENT: [
        Permission.CREATE_TICKET, Permission.READ_TICKET, Permission.UPDATE_TICKET
    ],
    UserRole.USER: [
        Permission.CREATE_TICKET, Permission.READ_TICKET
    ]
}

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token management
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
security_bearer = HTTPBearer(auto_error=False)

class SecurityManager:
    """Comprehensive security manager"""
    
    def __init__(self, config: SecurityConfig, redis_client: Optional[redis.Redis] = None):
        self.config = config
        self.redis = redis_client
        self.failed_attempts = {}
        self.blocked_ips = set()
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return pwd_context.hash(password)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password against security policy"""
        errors = []
        
        if len(password) < self.config.min_password_length:
            errors.append(f"Password must be at least {self.config.min_password_length} characters long")
        
        if self.config.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.config.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.config.require_digits and not re.search(r'\\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.config.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check common passwords
        common_passwords = {
            "password", "123456", "password123", "admin", "qwerty", 
            "letmein", "welcome", "monkey", "dragon"
        }
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength_score": self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> float:
        """Calculate password strength score (0-1)"""
        score = 0.0
        
        # Length score
        score += min(len(password) / 20, 0.25)
        
        # Character diversity
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        score += (has_lower + has_upper + has_digit + has_special) * 0.15
        
        # Entropy bonus
        unique_chars = len(set(password))
        score += min(unique_chars / len(password), 0.25) * 0.2
        
        return min(score, 1.0)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": str(uuid.uuid4())  # Unique token ID
        })
        
        return jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": str(uuid.uuid4())
        })
        
        return jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
            
            # Check if token is blacklisted (requires Redis)
            if self.redis:
                jti = payload.get("jti")
                if jti and await self.redis.get(f"blacklist:{jti}"):
                    return None
            
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    async def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist"""
        if not self.redis:
            return False
        
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti and exp:
                # Set expiry time for blacklist entry
                ttl = exp - int(datetime.utcnow().timestamp())
                if ttl > 0:
                    await self.redis.setex(f"blacklist:{jti}", ttl, "1")
                    return True
                    
        except JWTError:
            pass
        
        return False
    
    async def check_rate_limit(self, key: str, limit: int, window: int = 60) -> Dict[str, Any]:
        """Check rate limiting using sliding window"""
        if not self.redis:
            return {"allowed": True, "remaining": limit}
        
        try:
            current_time = int(time.time())
            pipeline = self.redis.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(f"rate_limit:{key}", 0, current_time - window)
            
            # Count current requests
            pipeline.zcard(f"rate_limit:{key}")
            
            # Add current request
            pipeline.zadd(f"rate_limit:{key}", {str(uuid.uuid4()): current_time})
            
            # Set expiry
            pipeline.expire(f"rate_limit:{key}", window)
            
            results = await pipeline.execute()
            current_count = results[1]
            
            remaining = max(0, limit - current_count)
            allowed = current_count < limit
            
            if not allowed:
                # Remove the request we just added since it's over limit
                await self.redis.zpopmax(f"rate_limit:{key}")
            
            return {
                "allowed": allowed,
                "remaining": remaining,
                "reset_time": current_time + window,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open in case of Redis issues
            return {"allowed": True, "remaining": limit}
    
    async def track_failed_login(self, identifier: str, ip_address: str) -> bool:
        """Track failed login attempts and implement progressive delays"""
        key = f"failed_login:{identifier}:{ip_address}"
        
        if self.redis:
            try:
                attempts = await self.redis.incr(key)
                await self.redis.expire(key, 3600)  # Reset after 1 hour
                
                # Progressive delays
                if attempts >= 5:
                    # Block for increasing duration
                    block_duration = min(attempts * 60, 3600)  # Max 1 hour
                    await self.redis.setex(f"blocked:{ip_address}", block_duration, str(attempts))
                    return False
                    
            except Exception as e:
                logger.error(f"Failed login tracking error: {e}")
        
        return True
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        if self.redis:
            try:
                blocked = await self.redis.get(f"blocked:{ip_address}")
                return blocked is not None
            except Exception as e:
                logger.error(f"IP blocking check error: {e}")
        
        return False
    
    def validate_ip_address(self, ip_address: str, allowed_networks: List[str] = None) -> bool:
        """Validate IP address against allowed networks"""
        if not allowed_networks:
            return True
        
        try:
            ip = ipaddress.ip_address(ip_address)
            for network in allowed_networks:
                if ip in ipaddress.ip_network(network):
                    return True
            return False
            
        except ValueError:
            return False
    
    def generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    async def create_user_session(self, user_id: str, user_agent: str, ip_address: str) -> str:
        """Create user session with metadata"""
        session_id = self.generate_session_id()
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "user_agent": user_agent,
            "ip_address": ip_address,
            "last_activity": datetime.utcnow().isoformat()
        }
        
        if self.redis:
            try:
                # Store session data
                await self.redis.setex(
                    f"session:{session_id}",
                    self.config.session_timeout_minutes * 60,
                    str(session_data)
                )
                
                # Track user sessions
                await self.redis.sadd(f"user_sessions:{user_id}", session_id)
                
                # Limit concurrent sessions
                sessions = await self.redis.smembers(f"user_sessions:{user_id}")
                if len(sessions) > self.config.max_concurrent_sessions:
                    # Remove oldest sessions
                    oldest_sessions = sorted(sessions)[:len(sessions) - self.config.max_concurrent_sessions]
                    for old_session in oldest_sessions:
                        await self.invalidate_session(old_session)
                
            except Exception as e:
                logger.error(f"Session creation error: {e}")
        
        return session_id
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate and refresh session"""
        if not self.redis:
            return None
        
        try:
            session_data = await self.redis.get(f"session:{session_id}")
            if not session_data:
                return None
            
            # Parse session data
            session_info = eval(session_data)  # In production, use json.loads
            
            # Update last activity
            session_info["last_activity"] = datetime.utcnow().isoformat()
            await self.redis.setex(
                f"session:{session_id}",
                self.config.session_timeout_minutes * 60,
                str(session_info)
            )
            
            return session_info
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        if not self.redis:
            return False
        
        try:
            # Get session info to find user
            session_data = await self.redis.get(f"session:{session_id}")
            if session_data:
                session_info = eval(session_data)  # In production, use json.loads
                user_id = session_info.get("user_id")
                
                # Remove from user sessions set
                if user_id:
                    await self.redis.srem(f"user_sessions:{user_id}", session_id)
            
            # Delete session
            await self.redis.delete(f"session:{session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False

# Global security manager instance
security_manager: Optional[SecurityManager] = None

def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    global security_manager
    if security_manager is None:
        # Initialize with configuration
        config = SecurityConfig()  # Load from environment in production
        security_manager = SecurityManager(config)
    return security_manager

# Authentication dependencies
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    security = get_security_manager()
    
    # Verify token
    payload = security.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user information"
        )
    
    # Check session if session ID provided
    session_id = payload.get("session_id")
    if session_id:
        session_info = await security.validate_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )
    
    # Check IP blocking
    client_ip = request.client.host
    if await security.is_ip_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="IP address temporarily blocked due to suspicious activity"
        )
    
    # Load user from database (implement based on your user model)
    # user = db.query(User).filter(User.id == user_id).first()
    # For now, return payload data
    
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role", UserRole.USER),
        "permissions": ROLE_PERMISSIONS.get(UserRole(payload.get("role", UserRole.USER)), []),
        "session_id": session_id
    }

def require_permissions(*required_permissions: Permission):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (FastAPI dependency injection)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_permissions = set(current_user.get("permissions", []))
            required_perms = set(required_permissions)
            
            if not required_perms.issubset(user_permissions):
                missing_perms = required_perms - user_permissions
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing: {', '.join(missing_perms)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(*allowed_roles: UserRole):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = UserRole(current_user.get("role", UserRole.USER))
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def rate_limit(operation: str, identifier: str, limit: Optional[int] = None):
    """Rate limiting dependency"""
    security = get_security_manager()
    
    if limit is None:
        limit = security.config.default_rate_limit
    
    result = await security.check_rate_limit(f"{operation}:{identifier}", limit)
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Rate limit exceeded",
                "limit": limit,
                "remaining": result["remaining"],
                "reset_time": result["reset_time"]
            }
        )

# Security middleware
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS for HTTPS
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Export key components
__all__ = [
    'SecurityManager', 'SecurityConfig', 'UserRole', 'Permission',
    'get_security_manager', 'get_current_user', 'require_permissions', 
    'require_role', 'rate_limit', 'security_headers_middleware'
]