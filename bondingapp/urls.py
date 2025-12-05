# """
# URL Configuration for Bonding App API
# Location: bondingapp/core/urls.py

# This file defines all API endpoints using DRF's DefaultRouter
# for automatic ViewSet registration and custom action routing.
# """

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from bondingapp.core.views import (
#     AuthViewSet,
#     UserViewSet,
#     ActivityViewSet,
#     ProgressViewSet,
#     RewardViewSet,
#     PartnerViewSet,
#     NotificationViewSet,
#     SettingsViewSet,
# )

# # Create the main router
# router = DefaultRouter()

# # ============================================
# # VIEWSET REGISTRATION
# # ============================================

# # Authentication ViewSet
# # Endpoints:
# #   POST   /api/auth/google-login/
# #   POST   /api/auth/register/
# #   POST   /api/auth/logout/
# router.register(r'auth', AuthViewSet, basename='auth')

# # User Management ViewSet
# # Endpoints:
# #   GET    /api/users/me/
# #   PUT    /api/users/update-profile/
# #   PATCH  /api/users/update-profile/
# #   POST   /api/users/partner/link/
# #   DELETE /api/users/partner/unlink/
# #   GET    /api/users/preferences/
# #   PUT    /api/users/preferences/
# router.register(r'users', UserViewSet, basename='users')

# # Activity ViewSet
# # Endpoints:
# #   GET    /api/activities/                     - List all activities
# #   GET    /api/activities/{id}/                - Get activity detail
# #   GET    /api/activities/daily/               - Today's featured activities
# #   GET    /api/activities/categories/          - All categories
# #   POST   /api/activities/{id}/start/          - Start activity session
# #   POST   /api/activities/{id}/complete/       - Complete activity
# #   POST   /api/activities/{id}/skip/           - Skip activity
# router.register(r'activities', ActivityViewSet, basename='activities')

# # Progress & Statistics ViewSet
# # Endpoints:
# #   GET    /api/progress/overview/              - Dashboard overview
# #   GET    /api/progress/streak/                - Streak information
# #   GET    /api/progress/bond-score/            - Bond score history
# #   GET    /api/progress/achievements/          - Badges & milestones
# #   GET    /api/progress/history/               - Activity history
# router.register(r'progress', ProgressViewSet, basename='progress')

# # Rewards & Gamification ViewSet
# # Endpoints:
# #   GET    /api/rewards/coins/                  - Coin balance & transactions
# #   POST   /api/rewards/spend-coins/            - Spend coins
# #   GET    /api/rewards/levels/                 - Level info & progress
# #   POST   /api/rewards/claim-daily-bonus/      - Claim daily bonus
# router.register(r'rewards', RewardViewSet, basename='rewards')

# # Partner Interaction ViewSet
# # Endpoints:
# #   GET    /api/partner/status/                 - Partner status
# #   GET    /api/partner/activity-status/        - Partner activity status
# #   GET    /api/partner/notifications/          - Partner notifications
# router.register(r'partner', PartnerViewSet, basename='partner')

# # Notification ViewSet
# # Endpoints:
# #   GET    /api/notifications/                  - List notifications
# #   GET    /api/notifications/{id}/             - Get notification detail
# #   POST   /api/notifications/{id}/mark-read/   - Mark as read
# #   POST   /api/notifications/mark-all-read/    - Mark all as read
# #   GET    /api/notifications/unread-count/     - Unread count
# router.register(r'notifications', NotificationViewSet, basename='notifications')

# # Settings ViewSet
# # Endpoints:
# #   GET    /api/settings/                       - Get all settings
# #   PUT    /api/settings/                       - Update settings
# #   PATCH  /api/settings/                       - Partial update settings
# router.register(r'settings', SettingsViewSet, basename='settings')


# # ============================================
# # URL PATTERNS
# # ============================================

# app_name = 'api'

# urlpatterns = [
#     # Include all router URLs under /api/ prefix
#     path('', include(router.urls)),
# ]


# # ============================================
# # ENDPOINT DOCUMENTATION
# # ============================================

# """
# COMPLETE API ENDPOINT REFERENCE
# ================================

# AUTHENTICATION
# --------------
# POST   /api/auth/google-login/
#     Body: {"google_token": "..."}
#     Response: {user, tokens: {access, refresh}, is_new_user}
    
# POST   /api/auth/register/
#     Body: {username, email, password, confirm_password, first_name, last_name, age, preferred_language}
#     Response: {user, tokens: {access, refresh}}
    
# POST   /api/auth/logout/
#     Headers: Authorization: Bearer <token>
#     Body: {"refresh_token": "..."}
#     Response: {success, message}


# USER MANAGEMENT
# ---------------
# GET    /api/users/me/
#     Headers: Authorization: Bearer <token>
#     Response: {success, user: {...}}
    
# PUT    /api/users/update-profile/
# PATCH  /api/users/update-profile/
#     Headers: Authorization: Bearer <token>
#     Body: {username?, first_name?, last_name?, age?, bio?, phone_number?, preferred_language?, theme?}
#     Response: {success, message, user}
    
# POST   /api/users/partner/link/
#     Headers: Authorization: Bearer <token>
#     Body: {"invitation_code": "ABC12345"}
#     Response: {success, message, partner}
    
# DELETE /api/users/partner/unlink/
#     Headers: Authorization: Bearer <token>
#     Response: {success, message}
    
# GET    /api/users/preferences/
#     Headers: Authorization: Bearer <token>
#     Response: {success, preferences: {...}}
    
# PUT    /api/users/preferences/
#     Headers: Authorization: Bearer <token>
#     Body: {daily_reminder_enabled?, daily_reminder_time?, partner_activity_alerts?, ...}
#     Response: {success, message, preferences}


# ACTIVITIES
# ----------
# GET    /api/activities/
#     Headers: Authorization: Bearer <token>
#     Query Params: ?category=uuid&difficulty=easy&mode=solo&premium=true
#     Response: {success, count, activities: [...]}
    
# GET    /api/activities/{id}/
#     Headers: Authorization: Bearer <token>
#     Response: {success, activity: {...}}
    
# GET    /api/activities/daily/
#     Headers: Authorization: Bearer <token>
#     Response: {success, count, activities: [...]}
    
# GET    /api/activities/categories/
#     Headers: Authorization: Bearer <token>
#     Response: {success, count, categories: [...]}
    
# POST   /api/activities/{id}/start/
#     Headers: Authorization: Bearer <token>
#     Body: {"mode": "solo" | "together"}
#     Response: {success, message, session: {...}}
    
# POST   /api/activities/{id}/complete/
#     Headers: Authorization: Bearer <token>
#     Body: {
#         session_id: uuid,
#         responses?: {...},
#         photos?: [...],
#         notes?: "...",
#         rating?: 1-5
#     }
#     Response: {success, message, completion, rewards: {points, coins, level}}
    
# POST   /api/activities/{id}/skip/
#     Headers: Authorization: Bearer <token>
#     Response: {success, message, skips_remaining}


# PROGRESS & STATISTICS
# ---------------------
# GET    /api/progress/overview/
#     Headers: Authorization: Bearer <token>
#     Response: {
#         success,
#         overview: {
#             total_activities_completed,
#             activities_this_week,
#             activities_this_month,
#             bond_score,
#             bond_score_change,
#             current_streak,
#             longest_streak,
#             total_points,
#             total_coins,
#             current_level,
#             badges_unlocked,
#             milestones_achieved,
#             favorite_category,
#             most_active_day,
#             partner_sync_rate
#         }
#     }
    
# GET    /api/progress/streak/
#     Headers: Authorization: Bearer <token>
#     Response: {success, streak: {...}}
    
# GET    /api/progress/bond-score/
#     Headers: Authorization: Bearer <token>
#     Response: {success, current_score, history: [...], trend}
    
# GET    /api/progress/achievements/
#     Headers: Authorization: Bearer <token>
#     Response: {
#         success,
#         badges: {unlocked: [...], all: [...], unlocked_count, total_count},
#         milestones: {achieved: [...], all: [...], achieved_count, total_count}
#     }
    
# GET    /api/progress/history/
#     Headers: Authorization: Bearer <token>
#     Query Params: ?limit=20&offset=0&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
#     Response: {success, count, next, previous, history: [...]}


# REWARDS & GAMIFICATION
# ----------------------
# GET    /api/rewards/coins/
#     Headers: Authorization: Bearer <token>
#     Response: {success, balance, transactions: [...]}
    
# POST   /api/rewards/spend-coins/
#     Headers: Authorization: Bearer <token>
#     Body: {
#         item_type: "unlock_activity" | "hint" | "theme" | "custom_activity",
#         item_id?: uuid,
#         cost: number
#     }
#     Response: {success, message, new_balance, transaction}
    
# GET    /api/rewards/levels/
#     Headers: Authorization: Bearer <token>
#     Response: {
#         success,
#         current_level,
#         level_name,
#         total_points,
#         progress_percentage,
#         points_to_next_level,
#         next_level,
#         all_levels: {...}
#     }
    
# POST   /api/rewards/claim-daily-bonus/
#     Headers: Authorization: Bearer <token>
#     Response: {success, message, coins_earned, new_balance, transaction}


# PARTNER INTERACTION
# -------------------
# GET    /api/partner/status/
#     Headers: Authorization: Bearer <token>
#     Response: {
#         success,
#         has_partner,
#         partner: {...},
#         is_online,
#         last_active,
#         current_activity,
#         activities_completed_today,
#         current_streak
#     }
    
# GET    /api/partner/activity-status/
#     Headers: Authorization: Bearer <token>
#     Query Params: ?activity_id=uuid
#     Response: {
#         success,
#         activity_id,
#         activity_title,
#         partner_completed,
#         partner_in_progress,
#         completed_at
#     }
    
# GET    /api/partner/notifications/
#     Headers: Authorization: Bearer <token>
#     Response: {success, count, notifications: [...]}


# NOTIFICATIONS
# -------------
# GET    /api/notifications/
#     Headers: Authorization: Bearer <token>
#     Query Params: ?unread_only=true&limit=20
#     Response: {success, count, notifications: [...]}
    
# GET    /api/notifications/{id}/
#     Headers: Authorization: Bearer <token>
#     Response: {success, notification: {...}}
    
# POST   /api/notifications/{id}/mark-read/
#     Headers: Authorization: Bearer <token>
#     Response: {success, message}
    
# POST   /api/notifications/mark-all-read/
#     Headers: Authorization: Bearer <token>
#     Response: {success, message, count}
    
# GET    /api/notifications/unread-count/
#     Headers: Authorization: Bearer <token>
#     Response: {success, unread_count}


# SETTINGS
# --------
# GET    /api/settings/
#     Headers: Authorization: Bearer <token>
#     Response: {
#         success,
#         settings: {
#             profile: {username, email, preferred_language, theme},
#             notifications: {...},
#             account: {has_partner, invitation_code, relationship_start_date}
#         }
#     }
    
# PUT    /api/settings/
# PATCH  /api/settings/
#     Headers: Authorization: Bearer <token>
#     Body: {
#         profile?: {preferred_language?, theme?},
#         notifications?: {daily_reminder_enabled?, partner_activity_alerts?, ...}
#     }
#     Response: {success, message}


# QUERY PARAMETER REFERENCE
# --------------------------
# Activities:
#     - category: UUID of category
#     - difficulty: easy | medium | deep
#     - mode: solo | together | both
#     - premium: true | false

# Progress History:
#     - limit: number (default: 20)
#     - offset: number (default: 0)
#     - date_from: YYYY-MM-DD
#     - date_to: YYYY-MM-DD

# Notifications:
#     - unread_only: true | false
#     - limit: number (default: 20)

# Partner Activity Status:
#     - activity_id: UUID (required)


# ERROR RESPONSES
# ---------------
# 400 Bad Request
#     {success: false, message: "...", error?: "..."}
    
# 401 Unauthorized
#     {detail: "Authentication credentials were not provided."}
    
# 402 Payment Required
#     {success: false, message: "Insufficient coins", required_coins, your_coins}
    
# 404 Not Found
#     {success: false, message: "..."}
    
# 429 Too Many Requests
#     {success: false, message: "Daily skip limit reached", skips_used, max_skips}


# AUTHENTICATION
# --------------
# All endpoints except /api/auth/google-login/ and /api/auth/register/
# require JWT authentication via Authorization header:

#     Authorization: Bearer <access_token>

# Token refresh is handled by djangorestframework-simplejwt separately.


# RATE LIMITING
# -------------
# Consider implementing rate limiting for:
# - Activity completions: 50/hour
# - Partner linking attempts: 10/hour
# - Coin spending: 20/hour


# CACHING
# -------
# The following endpoints use caching:
# - /api/activities/daily/ - 1 hour
# - /api/activities/categories/ - 24 hours

# Cache keys include user's preferred language for localization.
# """