from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId
import logging

from ..database import db
from ..models.activity import (
    ActivityResponse, ActivityFilters, UserActivitySummary, ActivityStats,
    ActivityType, ActivityCategory, UserInfo, ActivityContext, ActivityDetails
)
from ..middleware.auth import get_current_user, require_role
from ..models.user import UserRole

router = APIRouter(prefix="/activities", tags=["activity-tracking"])
logger = logging.getLogger(__name__)



@router.get("/", response_model=List[ActivityResponse])
@router.get("", response_model=List[ActivityResponse])
async def get_activities(
        activity_type: Optional[ActivityType] = Query(None, description="Filter by activity type"),
        category: Optional[ActivityCategory] = Query(None, description="Filter by category"),
        user_id: Optional[str] = Query(None, description="Filter by user ID"),
        username: Optional[str] = Query(None, description="Filter by username"),
        resource_type: Optional[str] = Query(None, description="Filter by resource type (recipe, user, etc.)"),
        resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
        date_from: Optional[datetime] = Query(None, description="Filter activities from this date"),
        date_to: Optional[datetime] = Query(None, description="Filter activities until this date"),
        skip: int = Query(0, ge=0, description="Number of activities to skip"),
        limit: int = Query(50, ge=1, le=200, description="Number of activities to return"),
        # current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))  # COMMENT THIS OUT
):
    """Get activities with filtering - Admin/Owner only"""
    try:
        # TEMPORARY: Create fake user for testing
        current_user = {"username": "test", "role": "admin"}  # ADD THIS LINE

        # Test if we can reach this point
        print(f"DEBUG: Function started, limit={limit}")  # ADD THIS LINE

        query = {}

        # Build query based on filters
        if activity_type:
            query["activity_type"] = activity_type.value
        if category:
            query["category"] = category.value
        if user_id:
            query["user_info.user_id"] = user_id
        if username:
            query["user_info.username"] = {"$regex": username, "$options": "i"}
        if resource_type:
            query["details.resource_type"] = resource_type
        if resource_id:
            query["details.resource_id"] = resource_id

        # Date range filtering
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query

        print(f"DEBUG: Query built: {query}")  # ADD THIS LINE

        # Execute query with pagination
        cursor = db.activities.find(query).skip(skip).limit(limit).sort("created_at", -1)
        activities = []

        print(f"DEBUG: About to process cursor")  # ADD THIS LINE

        for activity_doc in cursor:
            print(f"DEBUG: Processing activity {activity_doc.get('_id')}")  # ADD THIS LINE
            activities.append(_build_activity_response(activity_doc))

        print(f"DEBUG: Successfully processed {len(activities)} activities")  # ADD THIS LINE
        logger.info(f"Retrieved {len(activities)} activities for admin user {current_user['username']}")
        return activities

    except Exception as e:
        print(f"DEBUG: Exception occurred: {type(e).__name__}: {e}")  # ADD THIS LINE
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")  # ADD THIS LINE
        logger.error(f"Error retrieving activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activities")


@router.get("/my-activities", response_model=List[ActivityResponse])
async def get_my_activities(
        activity_type: Optional[ActivityType] = Query(None, description="Filter by activity type"),
        category: Optional[ActivityCategory] = Query(None, description="Filter by category"),
        date_from: Optional[datetime] = Query(None, description="Filter activities from this date"),
        date_to: Optional[datetime] = Query(None, description="Filter activities until this date"),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        current_user: dict = Depends(get_current_user)
):
    """Get current user's activities"""
    try:
        query = {"user_info.user_id": str(current_user["_id"])}

        # Apply filters
        if activity_type:
            query["activity_type"] = activity_type.value
        if category:
            query["category"] = category.value

        # Date range filtering
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query

        cursor = db.activities.find(query).skip(skip).limit(limit).sort("created_at", -1)
        activities = []

        for activity_doc in cursor:
            activities.append(_build_activity_response(activity_doc))

        logger.info(f"Retrieved {len(activities)} activities for user {current_user['username']}")
        return activities

    except Exception as e:
        logger.error(f"Error retrieving user activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve your activities")


@router.get("/user/{user_id}", response_model=UserActivitySummary)
async def get_user_activity_summary(
        user_id: str,
        days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Get activity summary for a specific user - Admin/Owner only"""
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        # Get user info
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Build base query
        base_query = {
            "user_info.user_id": user_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }

        # Get activity counts using aggregation
        pipeline = [
            {"$match": base_query},
            {
                "$group": {
                    "_id": "$activity_type",
                    "count": {"$sum": 1},
                    "last_activity": {"$max": "$created_at"}
                }
            }
        ]

        activity_counts = {}
        last_activity = None
        total_activities = 0

        for result in db.activities.aggregate(pipeline):
            activity_type = result["_id"]
            count = result["count"]
            activity_counts[activity_type] = count
            total_activities += count

            if not last_activity or result["last_activity"] > last_activity:
                last_activity = result["last_activity"]

        # Get last login specifically
        last_login = None
        login_activity = db.activities.find_one(
            {"user_info.user_id": user_id, "activity_type": "login"},
            sort=[("created_at", -1)]
        )
        if login_activity:
            last_login = login_activity["created_at"]

        # Get most recent activities (last 10)
        recent_activities = []
        cursor = db.activities.find(base_query).sort("created_at", -1).limit(10)
        for activity_doc in cursor:
            recent_activities.append(_build_activity_response(activity_doc))

        # Build summary
        summary = UserActivitySummary(
            user_id=user_id,
            username=user["username"],
            role=user["role"],
            last_login=last_login,
            last_activity=last_activity,
            total_activities=total_activities,
            login_count=activity_counts.get("login", 0),
            recipes_created=activity_counts.get("create_recipe", 0),
            recipes_updated=activity_counts.get("update_recipe", 0),
            recipes_deleted=activity_counts.get("delete_recipe", 0),
            favorites_added=activity_counts.get("favorite_recipe", 0),
            searches_performed=activity_counts.get("search_recipes", 0),
            admin_actions=activity_counts.get("view_admin", 0),
            most_recent_activities=recent_activities
        )

        logger.info(f"Generated activity summary for user {user['username']} ({days_back} days)")
        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating user activity summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate user activity summary")


@router.get("/stats/summary", response_model=ActivityStats)
async def get_activity_statistics(
        days_back: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Get system-wide activity statistics - Admin/Owner only"""
    try:
        # Calculate date ranges
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # Base query for the time period
        base_query = {"created_at": {"$gte": start_date, "$lte": end_date}}

        # Total activities
        total_activities = db.activities.count_documents(base_query)

        # Unique users
        unique_users = len(db.activities.distinct("user_info.user_id", base_query))

        # Activities by time period
        activities_today = db.activities.count_documents({
            "created_at": {"$gte": today_start}
        })
        activities_this_week = db.activities.count_documents({
            "created_at": {"$gte": week_start}
        })
        activities_this_month = db.activities.count_documents({
            "created_at": {"$gte": month_start}
        })

        # Activity by type
        type_pipeline = [
            {"$match": base_query},
            {"$group": {"_id": "$activity_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        activity_by_type = {}
        for result in db.activities.aggregate(type_pipeline):
            activity_by_type[result["_id"]] = result["count"]

        # Activity by category
        category_pipeline = [
            {"$match": base_query},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        activity_by_category = {}
        for result in db.activities.aggregate(category_pipeline):
            if result["_id"]:  # Skip null categories
                activity_by_category[result["_id"]] = result["count"]

        # Top users
        user_pipeline = [
            {"$match": base_query},
            {
                "$group": {
                    "_id": "$user_info.user_id",
                    "username": {"$first": "$user_info.username"},
                    "role": {"$first": "$user_info.role"},
                    "count": {"$sum": 1},
                    "last_activity": {"$max": "$created_at"}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_users = []
        for result in db.activities.aggregate(user_pipeline):
            top_users.append({
                "user_id": result["_id"],
                "username": result["username"],
                "role": result["role"],
                "activity_count": result["count"],
                "last_activity": result["last_activity"].isoformat()
            })

        # Hourly distribution (last 24 hours)
        hourly_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": today_start}
                }
            },
            {
                "$group": {
                    "_id": {"$hour": "$created_at"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        hourly_distribution = []
        hourly_data = {result["_id"]: result["count"] for result in db.activities.aggregate(hourly_pipeline)}
        for hour in range(24):
            hourly_distribution.append({
                "hour": hour,
                "count": hourly_data.get(hour, 0)
            })

        # Daily distribution (last 30 days)
        daily_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": month_start}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "day": {"$dayOfMonth": "$created_at"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        daily_distribution = []
        daily_data = {}
        for result in db.activities.aggregate(daily_pipeline):
            date_key = f"{result['_id']['year']}-{result['_id']['month']:02d}-{result['_id']['day']:02d}"
            daily_data[date_key] = result["count"]

        # Fill in missing days with 0
        current_date = month_start
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            daily_distribution.append({
                "date": date_key,
                "count": daily_data.get(date_key, 0)
            })
            current_date += timedelta(days=1)

        stats = ActivityStats(
            total_activities=total_activities,
            unique_users=unique_users,
            activities_today=activities_today,
            activities_this_week=activities_this_week,
            activities_this_month=activities_this_month,
            top_users=top_users,
            activity_by_type=activity_by_type,
            activity_by_category=activity_by_category,
            hourly_distribution=hourly_distribution,
            daily_distribution=daily_distribution
        )

        logger.info(f"Generated activity statistics for {days_back} days")
        return stats

    except Exception as e:
        logger.error(f"Error generating activity statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate activity statistics")


@router.get("/users/summary", response_model=List[UserActivitySummary])
async def get_all_users_activity_summary(
        days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
        active_only: bool = Query(False, description="Only show users with activity in the period"),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.OWNER]))
):
    """Get activity summary for all users - Admin/Owner only"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Get all users or just active users
        if active_only:
            # Get users who have activity in the time period
            active_user_ids = db.activities.distinct(
                "user_info.user_id",
                {"created_at": {"$gte": start_date, "$lte": end_date}}
            )
            user_query = {"_id": {"$in": [ObjectId(uid) for uid in active_user_ids if ObjectId.is_valid(uid)]}}
        else:
            user_query = {}

        users = list(db.users.find(user_query).skip(skip).limit(limit).sort("username", 1))
        summaries = []

        for user in users:
            user_id = str(user["_id"])

            # Get activity counts for this user
            base_query = {
                "user_info.user_id": user_id,
                "created_at": {"$gte": start_date, "$lte": end_date}
            }

            # Count activities by type
            pipeline = [
                {"$match": base_query},
                {
                    "$group": {
                        "_id": "$activity_type",
                        "count": {"$sum": 1},
                        "last_activity": {"$max": "$created_at"}
                    }
                }
            ]

            activity_counts = {}
            last_activity = None
            total_activities = 0

            for result in db.activities.aggregate(pipeline):
                activity_type = result["_id"]
                count = result["count"]
                activity_counts[activity_type] = count
                total_activities += count

                if not last_activity or result["last_activity"] > last_activity:
                    last_activity = result["last_activity"]

            # Get last login
            last_login = None
            login_activity = db.activities.find_one(
                {"user_info.user_id": user_id, "activity_type": "login"},
                sort=[("created_at", -1)]
            )
            if login_activity:
                last_login = login_activity["created_at"]

            # Skip users with no activity if active_only is True
            if active_only and total_activities == 0:
                continue

            summary = UserActivitySummary(
                user_id=user_id,
                username=user["username"],
                role=user["role"],
                last_login=last_login,
                last_activity=last_activity,
                total_activities=total_activities,
                login_count=activity_counts.get("login", 0),
                recipes_created=activity_counts.get("create_recipe", 0),
                recipes_updated=activity_counts.get("update_recipe", 0),
                recipes_deleted=activity_counts.get("delete_recipe", 0),
                favorites_added=activity_counts.get("favorite_recipe", 0),
                searches_performed=activity_counts.get("search_recipes", 0),
                admin_actions=activity_counts.get("view_admin", 0),
                most_recent_activities=[]  # Don't include detailed activities in bulk summary
            )

            summaries.append(summary)

        logger.info(f"Generated activity summaries for {len(summaries)} users")
        return summaries

    except Exception as e:
        logger.error(f"Error generating users activity summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate users activity summary")


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
        activity_id: str,
        current_user: dict = Depends(get_current_user)
):
    """Get a specific activity by ID"""
    try:
        if not ObjectId.is_valid(activity_id):
            raise HTTPException(status_code=400, detail="Invalid activity ID")

        activity_doc = db.activities.find_one({"_id": ObjectId(activity_id)})
        if not activity_doc:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Check permissions: user can see their own activities, admins can see all
        if (current_user["role"] not in ["admin", "owner"] and
                activity_doc["user_info"]["user_id"] != str(current_user["_id"])):
            raise HTTPException(status_code=403, detail="Not authorized to view this activity")

        return _build_activity_response(activity_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activity")


@router.delete("/{activity_id}")
async def delete_activity(
        activity_id: str,
        current_user: dict = Depends(require_role([UserRole.OWNER]))  # Only owners can delete
):
    """Delete an activity record - Owner only"""
    try:
        if not ObjectId.is_valid(activity_id):
            raise HTTPException(status_code=400, detail="Invalid activity ID")

        result = db.activities.delete_one({"_id": ObjectId(activity_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Activity not found")

        logger.info(f"Activity {activity_id} deleted by {current_user['username']}")
        return {"message": "Activity deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete activity")


@router.delete("/user/{user_id}")
async def delete_user_activities(
        user_id: str,
        days_back: Optional[int] = Query(None,
                                         description="Delete activities older than N days (if not specified, deletes all)"),
        current_user: dict = Depends(require_role([UserRole.OWNER]))  # Only owners can bulk delete
):
    """Delete all activities for a specific user - Owner only"""
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        # Build delete query
        delete_query = {"user_info.user_id": user_id}

        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            delete_query["created_at"] = {"$lt": cutoff_date}

        result = db.activities.delete_many(delete_query)

        logger.info(f"Deleted {result.deleted_count} activities for user {user_id} by {current_user['username']}")
        return {"message": f"Deleted {result.deleted_count} activities"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user activities")


def _build_activity_response(activity_doc: dict) -> ActivityResponse:
    """Helper function to build ActivityResponse from database document"""
    try:
        logger.debug(f"Building response for activity: {activity_doc.get('_id')}")

        # Validate activity_type
        activity_type_value = activity_doc["activity_type"]
        try:
            activity_type = ActivityType(activity_type_value)
        except ValueError as e:
            logger.error(f"Invalid activity_type '{activity_type_value}': {e}")
            raise ValueError(f"Invalid activity_type: {activity_type_value}")

        # Validate user_info
        user_info_doc = activity_doc["user_info"]
        try:
            user_info = UserInfo(**user_info_doc)
        except Exception as e:
            logger.error(f"Invalid user_info {user_info_doc}: {e}")
            raise ValueError(f"Invalid user_info: {e}")

        # Handle optional category
        category = None
        if activity_doc.get("category"):
            try:
                category = ActivityCategory(activity_doc["category"])
            except ValueError as e:
                logger.warning(f"Invalid category '{activity_doc['category']}': {e}")
                # Set to None instead of failing
                category = None

        # Handle optional context
        context = None
        if activity_doc.get("context"):
            try:
                context = ActivityContext(**activity_doc["context"])
            except Exception as e:
                logger.warning(f"Invalid context {activity_doc['context']}: {e}")
                # Set to None instead of failing
                context = None

        # Handle optional details
        details = None
        if activity_doc.get("details"):
            try:
                details = ActivityDetails(**activity_doc["details"])
            except Exception as e:
                logger.warning(f"Invalid details {activity_doc['details']}: {e}")
                # Set to None instead of failing
                details = None

        return ActivityResponse(
            id=str(activity_doc["_id"]),
            activity_type=activity_type,
            category=category,
            user_info=user_info,
            context=context,
            details=details,
            description=activity_doc.get("description"),
            tags=activity_doc.get("tags", []),
            metadata=activity_doc.get("metadata", {}),
            created_at=activity_doc["created_at"]
        )

    except Exception as e:
        logger.error(f"Failed to build activity response: {e}")
        logger.error(f"Document that caused error: {activity_doc}")
        raise