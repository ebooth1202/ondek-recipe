import time
import json
import logging
from datetime import datetime, timedelta
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
                # EXCLUDE OWNER USERS FROM ALL TRACKING
                if user_info.role.lower() == "owner":
                    print(f"🚫 TRACKING DEBUG: Skipping tracking for owner user: {user_info.username}")
                    return response

                processing_time = int((time.time() - start_time) * 1000)
                await self._track_activity(request, response, user_info, processing_time)

            return response

        except Exception as e:
            # Still try to track the activity even if request failed (but not for owners)
            if 'user_info' in locals() and user_info and user_info.user_id != "anonymous" and user_info.role.lower() != "owner":
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
            authorization = request.headers.get("Authorization")
            if not authorization:
                return self._get_anonymous_user()

            try:
                scheme, token = authorization.split()
                if scheme.lower() != "bearer":
                    return self._get_anonymous_user()
            except ValueError:
                return self._get_anonymous_user()

            # Import here to avoid circular imports
            from jose import jwt
            from ..database import db
            import os

            SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

            # Decode token
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                username = payload.get("sub")
                if not username:
                    return self._get_anonymous_user()

            except jwt.PyJWTError as e:
                return self._get_anonymous_user()

            # Get user from database
            if db is not None:
                user = db.users.find_one({"username": username})
                if user:
                    return UserInfo(
                        user_id=str(user["_id"]),
                        username=user["username"],
                        role=user["role"],
                        email=user.get("email")
                    )

        except Exception as e:
            logger.debug(f"Could not extract user info: {e}")

        return self._get_anonymous_user()

    def _get_anonymous_user(self) -> UserInfo:
        """Return anonymous user info"""
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
            session_id=request.headers.get("x-session-id"),
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
        """Track the user activity with deduplication"""
        try:
            # Determine activity type and category
            activity_type, category = self._determine_activity_type(request, response)

            if not activity_type:
                return  # Skip tracking if we can't determine activity type

            # For page navigation, implement deduplication
            if activity_type == ActivityType.PAGE_NAVIGATION:
                if await self._is_duplicate_navigation(user_info.user_id, request.url.path):
                    print(
                        f"🔄 TRACKING DEBUG: Skipping duplicate navigation to {request.url.path} for {user_info.username}")
                    return

            # Get activity context
            context = self._get_activity_context(request)

            # Build activity details (simplified)
            details = self._build_simplified_activity_details(request, response, processing_time, error)

            # Create activity record
            activity_create = ActivityCreate(
                activity_type=activity_type,
                user_info=user_info,
                context=context,
                details=details,
                category=category,
                description=self._generate_simplified_description(activity_type, details),
                tags=self._generate_simplified_tags(request, activity_type, category),
                metadata={"tracked_by": "middleware", "version": "2.0"}
            )

            # Save to database
            await self._save_activity(activity_create)

        except Exception as e:
            logger.error(f"Failed to track activity: {e}")

    def _determine_activity_type(self, request: Request, response: Optional[Response]) -> tuple[
        Optional[ActivityType], Optional[ActivityCategory]]:
        """Determine activity type and category based on request - SIMPLIFIED VERSION"""
        method = request.method.upper()
        path = request.url.path.lower()

        # Authentication activities (always track)
        if "/auth/login" in path and method == "POST":
            return ActivityType.LOGIN, ActivityCategory.AUTHENTICATION
        elif "/auth/logout" in path:
            return ActivityType.LOGOUT, ActivityCategory.AUTHENTICATION

        # Page navigation (only for GET requests to main pages)
        elif method == "GET" and response and response.status_code == 200:
            # Only track navigation to main application pages
            if self._is_main_page(path):
                return ActivityType.PAGE_NAVIGATION, ActivityCategory.NAVIGATION

        # Don't track other activities (like API calls, individual recipe views, etc.)
        return None, None

    def _is_main_page(self, path: str) -> bool:
        """Check if this is a main application page worth tracking"""
        main_pages = [
            "/",  # Dashboard/Home
            "/recipes",  # Recipe list page
            "/favorites",  # Favorites page
            "/admin",  # Admin dashboard
            "/admin/activities",  # Activity tracker
            "/admin/issues",  # Issue tracker
        ]

        # Check exact matches for main pages
        for main_page in main_pages:
            if path == main_page or (path.startswith(main_page) and main_page != "/"):
                return True

        return False

    async def _is_duplicate_navigation(self, user_id: str, current_path: str) -> bool:
        """Check if this is a duplicate navigation for the user"""
        try:
            # Look for the user's last page navigation within the last 30 minutes
            thirty_minutes_ago = datetime.now() - timedelta(minutes=30)

            last_navigation = db.activities.find_one(
                {
                    "user_info.user_id": user_id,
                    "activity_type": "page_navigation",
                    "details.endpoint": current_path,
                    "created_at": {"$gte": thirty_minutes_ago}
                },
                sort=[("created_at", -1)]
            )

            return last_navigation is not None

        except Exception as e:
            logger.error(f"Error checking navigation duplication: {e}")
            return False  # If error, don't skip tracking

    def _build_simplified_activity_details(self, request: Request, response: Optional[Response],
                                           processing_time: int, error: Optional[str] = None) -> ActivityDetails:
        """Build simplified activity details"""

        return ActivityDetails(
            method=request.method.upper(),
            endpoint=request.url.path,
            response_status=response.status_code if response else None,
            response_time_ms=processing_time
            # Remove other verbose details like query_params, request_data, etc.
        )

    def _generate_simplified_description(self, activity_type: ActivityType, details: ActivityDetails) -> str:
        """Generate simple, readable descriptions"""
        descriptions = {
            ActivityType.LOGIN: "User logged in",
            ActivityType.LOGOUT: "User logged out",
            ActivityType.PAGE_NAVIGATION: f"Visited {self._get_page_name(details.endpoint)}"
        }

        return descriptions.get(activity_type, f"Performed {activity_type.value} action")

    def _get_page_name(self, path: str) -> str:
        """Convert path to friendly page name"""
        page_names = {
            "/": "Dashboard",
            "/recipes": "Recipes",
            "/favorites": "Favorites",
            "/admin": "Admin Dashboard",
            "/admin/activities": "Activity Tracker",
            "/admin/issues": "Issue Tracker"
        }

        return page_names.get(path, path)

    def _generate_simplified_tags(self, request: Request, activity_type: ActivityType, category: ActivityCategory) -> \
    list[str]:
        """Generate simple tags"""
        tags = ["navigation-tracking", category.value]

        if activity_type == ActivityType.LOGIN:
            tags.append("session-start")
        elif activity_type == ActivityType.LOGOUT:
            tags.append("session-end")
        elif activity_type == ActivityType.PAGE_NAVIGATION:
            tags.append("page-visit")

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
                "context": activity_create.context.dict() if activity_create.context else None,
                "details": activity_create.details.dict() if activity_create.details else None,
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