import time
import json
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from urllib.parse import parse_qs, urlparse
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..database import db
from ..models.activity import (
    ActivityType, ActivityCategory, ActivityCreate,
    UserInfo, ActivityContext, ActivityDetails
)

logger = logging.getLogger(__name__)


class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, track_all_requests: bool = True):
        super().__init__(app)
        self.track_all_requests = track_all_requests

        # Endpoints to exclude from tracking (health checks, static files, etc.)
        self.excluded_endpoints = {
            "/health", "/docs", "/redoc", "/openapi.json",
            "/favicon.ico", "/static/", "/_next/", "/assets/",
            "/index.html", "/build/", "/frontend/"
        }

        # Sensitive fields to exclude from request logging
        self.sensitive_fields = {
            "password", "confirm_password", "current_password", "new_password",
            "token", "refresh_token", "access_token", "authorization",
            "secret", "key", "credential", "api_key"
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tracking for excluded endpoints
        if self._should_exclude_endpoint(request.url.path):
            return await call_next(request)

        start_time = time.time()
        response = None

        try:
            # Get user info before processing request
            user_info = await self._get_user_info(request)

            # Process the request
            response = await call_next(request)

            # Track the activity after successful response
            if user_info and user_info.user_id != "anonymous":
                processing_time = int((time.time() - start_time) * 1000)
                await self._track_activity(request, response, user_info, processing_time)

            return response

        except Exception as e:
            # Still try to track the activity even if request failed
            if 'user_info' in locals() and user_info and user_info.user_id != "anonymous":
                processing_time = int((time.time() - start_time) * 1000)
                await self._track_activity(request, None, user_info, processing_time, error=str(e))

            raise

    def _should_exclude_endpoint(self, path: str) -> bool:
        """Check if endpoint should be excluded from tracking"""
        return any(excluded in path for excluded in self.excluded_endpoints)

    async def _get_user_info(self, request: Request) -> Optional[UserInfo]:
        """Extract user info from request"""
        try:
            # Try to get user from authorization header
            from ..middleware.auth import get_current_user_from_request

            user = await get_current_user_from_request(request)
            if user:
                return UserInfo(
                    user_id=str(user["_id"]),
                    username=user["username"],
                    role=user["role"],
                    email=user.get("email")
                )
        except Exception as e:
            logger.debug(f"Could not extract user info: {e}")

        # Return anonymous user for unauthenticated requests
        return UserInfo(
            user_id="anonymous",
            username="anonymous",
            role="anonymous",
            email=None
        )

    def _get_activity_context(self, request: Request) -> ActivityContext:
        """Extract activity context from request"""
        user_agent = request.headers.get("user-agent", "")
        browser = self._detect_browser(user_agent)

        return ActivityContext(
            ip_address=self._get_client_ip(request),
            user_agent=user_agent,
            browser=browser,
            page=str(request.url.path),
            referrer=request.headers.get("referer"),
            session_id=request.headers.get("x-session-id"),  # If you track sessions
            timestamp=datetime.now()
        )

    def _detect_browser(self, user_agent: str) -> str:
        """Simple browser detection"""
        if "Chrome" in user_agent:
            return "Chrome"
        elif "Firefox" in user_agent:
            return "Firefox"
        elif "Safari" in user_agent:
            return "Safari"
        elif "Edge" in user_agent:
            return "Edge"
        else:
            return "Unknown"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, handling proxies"""
        # Check for forwarded headers first (if behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"

    async def _track_activity(self, request: Request, response: Optional[Response],
                              user_info: UserInfo, processing_time: int, error: Optional[str] = None):
        """Track the user activity"""
        try:
            # Determine activity type and category
            activity_type, category = self._determine_activity_type(request, response)

            if not activity_type:
                return  # Skip tracking if we can't determine activity type

            # Get activity context
            context = self._get_activity_context(request)

            # Build activity details
            details = await self._build_activity_details(request, response, processing_time, error)

            # Create activity record
            activity_create = ActivityCreate(
                activity_type=activity_type,
                user_info=user_info,
                context=context,
                details=details,
                category=category,
                description=self._generate_description(activity_type, details),
                tags=self._generate_tags(request, activity_type, category),
                metadata={"tracked_by": "middleware", "version": "1.0"}
            )

            # Save to database
            await self._save_activity(activity_create)

        except Exception as e:
            logger.error(f"Failed to track activity: {e}")

    def _determine_activity_type(self, request: Request, response: Optional[Response]) -> tuple[
        Optional[ActivityType], Optional[ActivityCategory]]:
        """Determine activity type and category based on request"""
        method = request.method.upper()
        path = request.url.path.lower()

        # Authentication activities
        if "/auth/login" in path and method == "POST":
            return ActivityType.LOGIN, ActivityCategory.AUTHENTICATION
        elif "/auth/logout" in path:
            return ActivityType.LOGOUT, ActivityCategory.AUTHENTICATION

        # Recipe management activities
        elif "/recipes" in path:
            if method == "POST" and path == "/recipes":
                return ActivityType.CREATE_RECIPE, ActivityCategory.RECIPE_MANAGEMENT
            elif method in ["PUT", "PATCH"] and "/recipes/" in path:
                return ActivityType.UPDATE_RECIPE, ActivityCategory.RECIPE_MANAGEMENT
            elif method == "DELETE" and "/recipes/" in path:
                return ActivityType.DELETE_RECIPE, ActivityCategory.RECIPE_MANAGEMENT
            elif method == "GET" and "/recipes/" in path and not path.endswith("/recipes"):
                return ActivityType.VIEW_RECIPE, ActivityCategory.RECIPE_MANAGEMENT
            elif method == "GET" and "/recipes" in path:
                return ActivityType.SEARCH_RECIPES, ActivityCategory.SEARCH_BROWSE

        # Favorite activities
        elif "/favorite" in path:
            if method in ["POST", "PUT"]:
                return ActivityType.FAVORITE_RECIPE, ActivityCategory.RECIPE_MANAGEMENT
            elif method == "DELETE":
                return ActivityType.UNFAVORITE_RECIPE, ActivityCategory.RECIPE_MANAGEMENT

        # User management activities
        elif "/users" in path:
            if method == "POST":
                return ActivityType.CREATE_USER, ActivityCategory.USER_MANAGEMENT
            elif method in ["PUT", "PATCH"]:
                return ActivityType.UPDATE_USER, ActivityCategory.USER_MANAGEMENT
            elif method == "DELETE":
                return ActivityType.DELETE_USER, ActivityCategory.USER_MANAGEMENT

        # Admin activities
        elif "/admin" in path or "/issues" in path:
            return ActivityType.VIEW_ADMIN, ActivityCategory.ADMIN_ACTION

        # File operations
        elif "/upload" in path or "files" in path:
            return ActivityType.UPLOAD_FILE, ActivityCategory.FILE_OPERATION

        # Export operations
        elif "/export" in path:
            return ActivityType.EXPORT_DATA, ActivityCategory.ADMIN_ACTION

        # General API access for other endpoints
        elif method == "GET":
            return ActivityType.API_ACCESS, ActivityCategory.SEARCH_BROWSE

        return None, None

    async def _build_activity_details(self, request: Request, response: Optional[Response],
                                      processing_time: int, error: Optional[str] = None) -> ActivityDetails:
        """Build detailed activity information"""

        # Parse query parameters
        query_params = dict(request.query_params) if request.query_params else None

        # Get request data (sanitized)
        request_data = await self._get_sanitized_request_data(request)

        # Extract resource information from path
        resource_id, resource_type = self._extract_resource_info(request.url.path)

        return ActivityDetails(
            method=request.method.upper(),
            endpoint=request.url.path,
            resource_id=resource_id,
            resource_type=resource_type,
            query_params=query_params,
            request_data=request_data,
            response_status=response.status_code if response else None,
            response_time_ms=processing_time,
            file_info=self._extract_file_info(request) if "/upload" in request.url.path else None
        )

    async def _get_sanitized_request_data(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get sanitized request data (excluding sensitive fields)"""
        try:
            # Only capture request body for non-GET requests
            if request.method.upper() == "GET":
                return None

            # Try to get JSON body
            try:
                body = await request.body()
                if not body:
                    return None

                # Parse JSON if possible
                try:
                    data = json.loads(body.decode())
                    return self._sanitize_data(data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If not JSON, just log that we had body data
                    return {"_body_size": len(body), "_content_type": request.headers.get("content-type")}

            except Exception:
                return None

        except Exception as e:
            logger.debug(f"Could not extract request data: {e}")
            return None

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from data"""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            if key.lower() in self.sensitive_fields:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_data(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value

        return sanitized

    def _extract_resource_info(self, path: str) -> tuple[Optional[str], Optional[str]]:
        """Extract resource ID and type from URL path"""
        path_parts = path.strip("/").split("/")

        if "recipes" in path_parts:
            idx = path_parts.index("recipes")
            resource_type = "recipe"
            if len(path_parts) > idx + 1 and path_parts[idx + 1]:
                resource_id = path_parts[idx + 1]
                return resource_id, resource_type
            return None, resource_type

        elif "users" in path_parts:
            idx = path_parts.index("users")
            resource_type = "user"
            if len(path_parts) > idx + 1 and path_parts[idx + 1] != "me":
                resource_id = path_parts[idx + 1]
                return resource_id, resource_type
            return None, resource_type

        return None, None

    def _extract_file_info(self, request: Request) -> Optional[Dict[str, str]]:
        """Extract file information for upload operations"""
        try:
            content_type = request.headers.get("content-type", "")
            if "multipart/form-data" in content_type:
                return {
                    "content_type": content_type,
                    "content_length": request.headers.get("content-length", "unknown")
                }
        except Exception:
            pass
        return None

    def _generate_description(self, activity_type: ActivityType, details: ActivityDetails) -> str:
        """Generate human-readable description"""
        descriptions = {
            ActivityType.LOGIN: "User logged in",
            ActivityType.LOGOUT: "User logged out",
            ActivityType.CREATE_RECIPE: f"Created recipe via {details.endpoint}",
            ActivityType.UPDATE_RECIPE: f"Updated recipe {details.resource_id or 'unknown'}",
            ActivityType.DELETE_RECIPE: f"Deleted recipe {details.resource_id or 'unknown'}",
            ActivityType.VIEW_RECIPE: f"Viewed recipe {details.resource_id or 'unknown'}",
            ActivityType.FAVORITE_RECIPE: f"Favorited recipe {details.resource_id or 'unknown'}",
            ActivityType.UNFAVORITE_RECIPE: f"Unfavorited recipe {details.resource_id or 'unknown'}",
            ActivityType.SEARCH_RECIPES: "Searched for recipes",
            ActivityType.UPLOAD_FILE: "Uploaded file",
            ActivityType.VIEW_ADMIN: "Accessed admin area",
            ActivityType.API_ACCESS: f"Accessed {details.endpoint}"
        }

        return descriptions.get(activity_type, f"Performed {activity_type.value} action")

    def _generate_tags(self, request: Request, activity_type: ActivityType, category: ActivityCategory) -> list[str]:
        """Generate tags for the activity"""
        tags = ["auto-tracked", category.value]

        # Add method tag
        tags.append(request.method.lower())

        # Add specific tags based on activity type
        if activity_type in [ActivityType.CREATE_RECIPE, ActivityType.UPDATE_RECIPE, ActivityType.DELETE_RECIPE]:
            tags.append("recipe-modification")
        elif activity_type in [ActivityType.FAVORITE_RECIPE, ActivityType.UNFAVORITE_RECIPE]:
            tags.append("user-preference")
        elif activity_type == ActivityType.SEARCH_RECIPES:
            tags.append("search")

        return tags

    async def _save_activity(self, activity_create: ActivityCreate):
        """Save activity to database"""
        try:
            if db is None:
                logger.warning("Database not available for activity tracking")
                return

            activity_doc = {
                "activity_type": activity_create.activity_type.value,
                "category": activity_create.category.value if activity_create.category else None,
                "user_info": activity_create.user_info.dict(),
                "context": activity_create.context.dict(),
                "details": activity_create.details.dict(),
                "description": activity_create.description,
                "tags": activity_create.tags,
                "metadata": activity_create.metadata,
                "created_at": datetime.now()
            }

            # Insert into activities collection
            result = db.activities.insert_one(activity_doc)

            if result.inserted_id:
                logger.debug(
                    f"Activity tracked: {activity_create.activity_type.value} by {activity_create.user_info.username}")

        except Exception as e:
            logger.error(f"Failed to save activity to database: {e}")


# Helper function to get user from request (reuse from error_tracking.py if needed)
async def get_current_user_from_request(request: Request) -> Optional[dict]:
    """Get current user from request without using Depends"""
    try:
        from jose import jwt
        from ..database import db
        import os

        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

        # Try to get token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
        except ValueError:
            return None

        # Decode token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            username = payload.get("sub")
            if not username:
                return None
        except jwt.PyJWTError:
            return None

        # Get user from database
        if db is not None:
            user = db.users.find_one({"username": username})
            return user

    except Exception as e:
        logger.error(f"Error getting user from request: {e}")

    return None