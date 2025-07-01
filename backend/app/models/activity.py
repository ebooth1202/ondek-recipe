from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PAGE_NAVIGATION = "page_navigation"  # ADD THIS NEW TYPE
    # Keep existing types for backwards compatibility
    CREATE_RECIPE = "create_recipe"
    UPDATE_RECIPE = "update_recipe"
    DELETE_RECIPE = "delete_recipe"
    VIEW_RECIPE = "view_recipe"
    FAVORITE_RECIPE = "favorite_recipe"
    UNFAVORITE_RECIPE = "unfavorite_recipe"
    SEARCH_RECIPES = "search_recipes"
    UPLOAD_FILE = "upload_file"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    VIEW_ADMIN = "view_admin"
    EXPORT_DATA = "export_data"
    SYSTEM_ACTION = "system_action"
    API_ACCESS = "api_access"


class ActivityCategory(str, Enum):
    AUTHENTICATION = "authentication"
    NAVIGATION = "navigation"  # ADD THIS NEW CATEGORY
    # Keep existing categories
    RECIPE_MANAGEMENT = "recipe_management"
    USER_MANAGEMENT = "user_management"
    SEARCH_BROWSE = "search_browse"
    ADMIN_ACTION = "admin_action"
    FILE_OPERATION = "file_operation"
    SYSTEM = "system"


class UserInfo(BaseModel):
    user_id: str
    username: str
    role: str
    email: Optional[str] = None


class ActivityContext(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    page: Optional[str] = None
    referrer: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ActivityDetails(BaseModel):
    method: str  # GET, POST, PUT, DELETE
    endpoint: str  # /recipes, /users/me, etc.
    resource_id: Optional[str] = None  # ID of recipe, user, etc.
    resource_name: Optional[str] = None  # Name of recipe, username, etc.
    resource_type: Optional[str] = None  # recipe, user, file, etc.
    previous_values: Optional[Dict[str, Any]] = None  # For updates/deletes
    new_values: Optional[Dict[str, Any]] = None  # For creates/updates
    query_params: Optional[Dict[str, Any]] = None
    request_data: Optional[Dict[str, Any]] = None  # Sanitized request body
    response_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    file_info: Optional[Dict[str, str]] = None  # filename, size, type for uploads


class ActivityCreate(BaseModel):
    activity_type: ActivityType
    user_info: UserInfo
    context: ActivityContext
    details: ActivityDetails
    category: Optional[ActivityCategory] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class ActivityResponse(BaseModel):
    id: str
    activity_type: ActivityType
    category: Optional[ActivityCategory] = None  # Make optional
    user_info: UserInfo
    context: Optional[ActivityContext] = None    # Make optional
    details: Optional[ActivityDetails] = None    # Make optional
    description: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ActivityFilters(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    activity_type: Optional[ActivityType] = None
    category: Optional[ActivityCategory] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    ip_address: Optional[str] = None
    tags: Optional[List[str]] = None


class UserActivitySummary(BaseModel):
    user_id: str
    username: str
    role: str
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    total_activities: int = 0
    login_count: int = 0
    recipes_created: int = 0
    recipes_updated: int = 0
    recipes_deleted: int = 0
    favorites_added: int = 0
    searches_performed: int = 0
    admin_actions: int = 0
    most_recent_activities: List[ActivityResponse] = []


class ActivityStats(BaseModel):
    total_activities: int = 0
    unique_users: int = 0
    activities_today: int = 0
    activities_this_week: int = 0
    activities_this_month: int = 0
    top_users: List[Dict[str, Any]] = []
    activity_by_type: Dict[str, int] = {}
    activity_by_category: Dict[str, int] = {}
    hourly_distribution: List[Dict[str, Any]] = []
    daily_distribution: List[Dict[str, Any]] = []