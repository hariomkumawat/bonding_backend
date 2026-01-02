"""
DRF ViewSets for Bonding App
Location: bondingapp/core/views.py
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, datetime
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings

from bondingapp.models import (
    User, UserPreference, ActivityCategory, Activity,
    ActivitySession, ActivityCompletion, Streak, Badge,
    UserBadge, Milestone, UserMilestone, Notification,
    CoinTransaction, SkipLimit
)
from bondingapp.core.serializers import (
    UserSerializer, UserRegistrationSerializer, GoogleAuthSerializer,
    PartnerLinkSerializer, UserPreferenceSerializer,
    ActivityCategorySerializer, ActivityListSerializer, ActivityDetailSerializer,
    ActivitySessionSerializer, ActivityCompletionSerializer,
    ActivityCompletionHistorySerializer, StreakSerializer, BadgeSerializer,
    UserBadgeSerializer, MilestoneSerializer, UserMilestoneSerializer,
    CoinTransactionSerializer, CoinSpendSerializer, NotificationSerializer,EmailLoginSerializer,
    ProgressOverviewSerializer, BondScoreHistorySerializer,
    PartnerStatusSerializer, PartnerActivityStatusSerializer
)
from django.shortcuts import render
User = get_user_model()


# ============================================
# AUTHENTICATION VIEWSET
# ============================================

class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication operations
    Endpoints: google-login, register, logout, refresh-token
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer
    
    @action(detail=False, methods=['post'], url_path='google-login')
    def google_login(self, request):
        """
        Google OAuth login/signup
        POST /api/auth/google-login/
        Body: {"google_token": "..."}
        """
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        google_token = serializer.validated_data['google_token']
        
        try:
            # Verify Google token
            idinfo = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
            
            # Get user info from Google
            email = idinfo.get('email')
            google_id = idinfo.get('sub')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            profile_picture = idinfo.get('picture', '')
            
            # Check if user exists
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'google_id': google_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'profile_picture': profile_picture,
                }
            )
            
            if created:
                # New user - create preferences and generate invitation code
                UserPreference.objects.create(user=user)
                user.generate_invitation_code()
                
                # Create initial streak
                Streak.objects.create(user=user)
            
            # Update last login
            user.is_online = True
            user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'is_new_user': created,
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'message': 'Invalid Google token',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Manual registration (if needed)
        POST /api/auth/register/
        """
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Registration successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Email/Password login
        POST /api/auth/login/
        Body: {
            "email": "user@example.com",
            "password": "password123"
        }
        """
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            # Get user by email
            user = User.objects.get(email=email)
            
            # Check password
            if not user.check_password(password):
                return Response({
                    'success': False,
                    'message': 'Invalid email or password',
                    'message_hi': 'अमान्य ईमेल या पासवर्ड'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if account is active
            if not user.is_active:
                return Response({
                    'success': False,
                    'message': 'Account is inactive',
                    'message_hi': 'खाता निष्क्रिय है'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Update user status
            user.is_online = True
            user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'message_hi': 'लॉगिन सफल',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid email or password',
                'message_hi': 'अमान्य ईमेल या पासवर्ड'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user
        POST /api/auth/logout/
        """
        try:
            # Mark user as offline
            request.user.is_online = False
            request.user.save()
            
            # Blacklist refresh token if provided
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Logout failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# USER VIEWSET
# ============================================

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user operations
    Endpoints: me, update-profile, partner-link, partner-unlink, preferences
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to only show current user"""
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user profile
        GET /api/users/me/
        """
        serializer = UserSerializer(request.user, context={'request': request})
        return Response({
            'success': True,
            'user': serializer.data
        })
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Update user profile
        PUT/PATCH /api/users/update-profile/
        """
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='partner/link')
    def partner_link(self, request):
        """
        Link partner using invitation code
        POST /api/users/partner/link/
        Body: {"invitation_code": "ABC12345"}
        """
        serializer = PartnerLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        invitation_code = serializer.validated_data['invitation_code']
        
        # Check if user already has a partner
        if request.user.partner:
            return Response({
                'success': False,
                'message': 'You already have a partner linked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find partner by invitation code
        try:
            partner = User.objects.get(partner_invitation_code=invitation_code)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid invitation code'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Can't link to yourself
        if partner.id == request.user.id:
            return Response({
                'success': False,
                'message': 'Cannot link to yourself'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if partner already has a partner
        if partner.partner:
            return Response({
                'success': False,
                'message': 'This user already has a partner'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Link partners
        request.user.partner = partner
        partner.partner = request.user
        request.user.save()
        partner.save()
        
        # Create notification for partner
        Notification.objects.create(
            user=partner,
            notification_type='partner_joined',
            title_en=f'{request.user.username} is now your partner!',
            title_hi=f'{request.user.username} अब आपके साथी हैं!',
            message_en=f'{request.user.username} has accepted your invitation.',
            message_hi=f'{request.user.username} ने आपका निमंत्रण स्वीकार किया है।',
            data={'partner_id': str(request.user.id)}
        )
        
        return Response({
            'success': True,
            'message': 'Partner linked successfully',
            'partner': UserSerializer(partner).data
        })
    
    @action(detail=False, methods=['delete'], url_path='partner/unlink')
    def partner_unlink(self, request):
        """
        Unlink partner
        DELETE /api/users/partner/unlink/
        """
        if not request.user.partner:
            return Response({
                'success': False,
                'message': 'No partner to unlink'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        partner = request.user.partner
        
        # Unlink both users
        request.user.partner = None
        partner.partner = None
        request.user.save()
        partner.save()
        
        return Response({
            'success': True,
            'message': 'Partner unlinked successfully'
        })
    
    @action(detail=False, methods=['get', 'put'])
    def preferences(self, request):
        """
        Get or update user preferences
        GET/PUT /api/users/preferences/
        """
        preference, created = UserPreference.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            serializer = UserPreferenceSerializer(preference)
            return Response({
                'success': True,
                'preferences': serializer.data
            })
        
        elif request.method == 'PUT':
            serializer = UserPreferenceSerializer(
                preference,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'success': True,
                'message': 'Preferences updated successfully',
                'preferences': serializer.data
            })


# ============================================
# ACTIVITY VIEWSET
# ============================================

class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for activities
    Endpoints: list, retrieve, daily, categories, start, complete, skip
    """
    queryset = Activity.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ActivityDetailSerializer
        return ActivityListSerializer
    
    def get_queryset(self):
        queryset = Activity.objects.filter(is_active=True)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filter by mode
        mode = self.request.query_params.get('mode')
        if mode:
            queryset = queryset.filter(Q(mode=mode) | Q(mode='both'))
        
        # Filter premium
        show_premium = self.request.query_params.get('premium', 'true').lower() == 'true'
        if not show_premium:
            queryset = queryset.filter(is_premium=False)
        
        return queryset.select_related('category')
    
    def list(self, request, *args, **kwargs):
        """
        List all activities
        GET /api/activities/
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'activities': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get single activity detail
        GET /api/activities/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'activity': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def daily(self, request):
        """
        Get today's featured activities
        GET /api/activities/daily/
        """
        # Try to get from cache first
        cache_key = f'daily_activities_{request.user.preferred_language}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response({
                'success': True,
                'activities': cached_data
            })
        
        # Get daily featured activities
        daily_activities = Activity.objects.filter(
            is_active=True,
            is_daily_featured=True
        ).select_related('category')[:5]
        
        serializer = ActivityListSerializer(
            daily_activities,
            many=True,
            context={'request': request}
        )
        
        # Cache for 1 hour
        cache.set(cache_key, serializer.data, 3600)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'activities': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Get all activity categories
        GET /api/activities/categories/
        """
        cache_key = f'categories_{request.user.preferred_language}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response({
                'success': True,
                'categories': cached_data
            })
        
        categories = ActivityCategory.objects.filter(is_active=True)
        serializer = ActivityCategorySerializer(
            categories,
            many=True,
            context={'request': request}
        )
        
        # Cache for 24 hours
        cache.set(cache_key, serializer.data, 86400)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'categories': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start an activity session
        POST /api/activities/{id}/start/
        Body: {"mode": "solo" or "together"}
        """
        activity = self.get_object()
        mode = request.data.get('mode', 'solo')
        
        # Check if activity is premium and unlocked
        if activity.is_premium:
            is_unlocked = ActivityCompletion.objects.filter(
                user=request.user,
                activity=activity
            ).exists()
            
            if not is_unlocked and request.user.coins < activity.unlock_cost_coins:
                return Response({
                    'success': False,
                    'message': 'Insufficient coins to unlock this activity',
                    'required_coins': activity.unlock_cost_coins,
                    'your_coins': request.user.coins
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check if already in progress
        existing_session = ActivitySession.objects.filter(
            user=request.user,
            activity=activity,
            status__in=['started', 'in_progress']
        ).first()
        
        if existing_session:
            serializer = ActivitySessionSerializer(existing_session)
            return Response({
                'success': True,
                'message': 'Activity already in progress',
                'session': serializer.data
            })
        
        # Create new session
        session = ActivitySession.objects.create(
            user=request.user,
            activity=activity,
            mode=mode,
            status='started'
        )
        
        serializer = ActivitySessionSerializer(session)
        
        # Notify partner if together mode
        if mode == 'together' and request.user.partner:
            Notification.objects.create(
                user=request.user.partner,
                notification_type='partner_activity',
                title_en=f'{request.user.username} started an activity',
                title_hi=f'{request.user.username} ने एक गतिविधि शुरू की',
                message_en=f'Join them in "{activity.title_en}"',
                message_hi=f'उनके साथ "{activity.title_hi}" में शामिल हों',
                data={'activity_id': str(activity.id), 'session_id': str(session.id)}
            )
        
        return Response({
            'success': True,
            'message': 'Activity session started',
            'session': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete an activity
        POST /api/activities/{id}/complete/
        Body: {
            "session_id": "uuid",
            "responses": {...},
            "photos": [...],
            "notes": "...",
            "rating": 5
        }
        """
        activity = self.get_object()
        
        serializer = ActivityCompletionSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        completion = serializer.save()
        
        # Notify partner
        if request.user.partner:
            Notification.objects.create(
                user=request.user.partner,
                notification_type='partner_activity',
                title_en=f'{request.user.username} completed an activity',
                title_hi=f'{request.user.username} ने एक गतिविधि पूरी की',
                message_en=f'They completed "{activity.title_en}"',
                message_hi=f'उन्होंने "{activity.title_hi}" पूरा किया',
                data={'activity_id': str(activity.id), 'completion_id': str(completion.id)}
            )
        
        return Response({
            'success': True,
            'message': 'Activity completed successfully',
            'completion': ActivityCompletionSerializer(completion).data,
            'rewards': {
                'points': completion.points_earned,
                'coins': completion.coins_earned,
                'new_total_points': request.user.total_points,
                'new_total_coins': request.user.coins,
                'level': request.user.current_level
            }
        })
    
    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """
        Skip an activity
        POST /api/activities/{id}/skip/
        """
        activity = self.get_object()
        today = timezone.now().date()
        
        # Check skip limit
        skip_limit, created = SkipLimit.objects.get_or_create(
            user=request.user,
            date=today
        )
        
        if not skip_limit.can_skip():
            return Response({
                'success': False,
                'message': f'Daily skip limit reached ({skip_limit.max_skips_per_day} skips per day)',
                'skips_used': skip_limit.skips_used,
                'max_skips': skip_limit.max_skips_per_day
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Increment skip counter
        skip_limit.skips_used += 1
        skip_limit.save()
        
        # Update any active session
        ActivitySession.objects.filter(
            user=request.user,
            activity=activity,
            status__in=['started', 'in_progress']
        ).update(status='skipped')
        
        return Response({
            'success': True,
            'message': 'Activity skipped',
            'skips_remaining': skip_limit.max_skips_per_day - skip_limit.skips_used
        })


# ============================================
# PROGRESS VIEWSET
# ============================================

class ProgressViewSet(viewsets.GenericViewSet):
    """
    ViewSet for progress and statistics
    Endpoints: overview, streak, bond-score, achievements, history
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get overall progress overview
        GET /api/progress/overview/
        """
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Get activity counts
        total_activities = ActivityCompletion.objects.filter(user=user).count()
        activities_this_week = ActivityCompletion.objects.filter(
            user=user,
            completed_at__date__gte=week_ago
        ).count()
        activities_this_month = ActivityCompletion.objects.filter(
            user=user,
            completed_at__date__gte=month_ago
        ).count()
        
        # Bond score
        bond_score = user.calculate_bond_score()
        
        # Bond score change (compare with last week)
        # Simplified - you can implement more sophisticated tracking
        bond_score_change = 0  # TODO: Implement historical tracking
        
        # Streak
        streak = Streak.objects.filter(user=user).first()
        current_streak = streak.current_streak if streak else 0
        longest_streak = streak.longest_streak if streak else 0
        
        # Badges and milestones
        badges_unlocked = UserBadge.objects.filter(user=user).count()
        milestones_achieved = UserMilestone.objects.filter(user=user).count()
        
        # Favorite category
        favorite_category = ActivityCompletion.objects.filter(user=user).values(
            'activity__category__name_en'
        ).annotate(count=Count('id')).order_by('-count').first()
        
        favorite_category_name = favorite_category['activity__category__name_en'] if favorite_category else 'None'
        
        # Most active day
        most_active_day = ActivityCompletion.objects.filter(user=user).extra(
            select={'day': 'strftime("%%w", completed_at)'}
        ).values('day').annotate(count=Count('id')).order_by('-count').first()
        
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        most_active_day_name = days[int(most_active_day['day'])] if most_active_day else 'None'
        
        # Partner sync rate
        partner_sync_rate = 0
        if user.partner:
            user_completions = set(ActivityCompletion.objects.filter(
                user=user,
                completed_at__date__gte=month_ago
            ).values_list('activity_id', flat=True))
            
            partner_completions = set(ActivityCompletion.objects.filter(
                user=user.partner,
                completed_at__date__gte=month_ago
            ).values_list('activity_id', flat=True))
            
            if user_completions:
                partner_sync_rate = len(user_completions & partner_completions) / len(user_completions) * 100
        
        data = {
            'total_activities_completed': total_activities,
            'activities_this_week': activities_this_week,
            'activities_this_month': activities_this_month,
            'bond_score': bond_score,
            'bond_score_change': bond_score_change,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_points': user.total_points,
            'total_coins': user.coins,
            'current_level': user.current_level,
            'badges_unlocked': badges_unlocked,
            'milestones_achieved': milestones_achieved,
            'favorite_category': favorite_category_name,
            'most_active_day': most_active_day_name,
            'partner_sync_rate': round(partner_sync_rate, 2)
        }
        
        return Response({
            'success': True,
            'overview': data
        })
    
    @action(detail=False, methods=['get'])
    def streak(self, request):
        """
        Get current streak information
        GET /api/progress/streak/
        """
        streak, created = Streak.objects.get_or_create(user=request.user)
        serializer = StreakSerializer(streak)
        
        return Response({
            'success': True,
            'streak': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='bond-score')
    def bond_score(self, request):
        """
        Get bond score history
        GET /api/progress/bond-score/
        """
        # Get last 30 days of bond score
        # For simplicity, calculating current bond score
        # In production, you'd store daily snapshots
        
        current_score = request.user.calculate_bond_score()
        
        history = [
            {
                'date': timezone.now().date(),
                'score': current_score
            }
        ]
        
        return Response({
            'success': True,
            'current_score': current_score,
            'history': history,
            'trend': 'stable'  # Can be 'up', 'down', 'stable'
        })
    
    @action(detail=False, methods=['get'])
    def achievements(self, request):
        """
        Get all badges and milestones
        GET /api/progress/achievements/
        """
        # Unlocked badges
        user_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
        unlocked_badges = UserBadgeSerializer(user_badges, many=True).data
        
        # All badges (to show locked ones)
        all_badges = Badge.objects.filter(is_active=True)
        all_badges_data = BadgeSerializer(
            all_badges,
            many=True,
            context={'request': request}
        ).data
        
        # Achieved milestones
        user_milestones = UserMilestone.objects.filter(user=request.user).select_related('milestone')
        achieved_milestones = UserMilestoneSerializer(user_milestones, many=True).data
        
        # All milestones
        all_milestones = Milestone.objects.filter(is_active=True)
        all_milestones_data = MilestoneSerializer(
            all_milestones,
            many=True,
            context={'request': request}
        ).data
        
        return Response({
            'success': True,
            'badges': {
                'unlocked': unlocked_badges,
                'all': all_badges_data,
                'unlocked_count': len(unlocked_badges),
                'total_count': len(all_badges_data)
            },
            'milestones': {
                'achieved': achieved_milestones,
                'all': all_milestones_data,
                'achieved_count': len(achieved_milestones),
                'total_count': len(all_milestones_data)
            }
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get activity completion history
        GET /api/progress/history/
        Query params: ?limit=20&offset=0&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
        """
        queryset = ActivityCompletion.objects.filter(
            user=request.user
        ).select_related('activity', 'activity__category')
        
        # Date filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(completed_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(completed_at__date__lte=date_to)
        
        # Pagination
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        total_count = queryset.count()
        completions = queryset[offset:offset + limit]
        
        serializer = ActivityCompletionHistorySerializer(completions, many=True)
        
        return Response({
            'success': True,
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'history': serializer.data
        })


# ============================================
# REWARDS VIEWSET
# ============================================

class RewardViewSet(viewsets.GenericViewSet):
    """
    ViewSet for rewards and gamification
    Endpoints: coins, spend-coins, levels, claim-daily-bonus
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def coins(self, request):
        """
        Get coin balance and transaction history
        GET /api/rewards/coins/
        """
        user = request.user
        
        # Get recent transactions
        transactions = CoinTransaction.objects.filter(user=user)[:20]
        transaction_data = CoinTransactionSerializer(transactions, many=True).data
        
        return Response({
            'success': True,
            'balance': user.coins,
            'transactions': transaction_data
        })
    
    @action(detail=False, methods=['post'], url_path='spend-coins')
    def spend_coins(self, request):
        """
        Spend coins to unlock features
        POST /api/rewards/spend-coins/
        Body: {
            "item_type": "unlock_activity",
            "item_id": "uuid",
            "cost": 50
        }
        """
        serializer = CoinSpendSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        item_type = serializer.validated_data['item_type']
        cost = serializer.validated_data['cost']
        item_id = serializer.validated_data.get('item_id')
        
        # Deduct coins
        user.coins -= cost
        user.save()
        
        # Create transaction
        transaction = CoinTransaction.objects.create(
            user=user,
            transaction_type=f'spent_{item_type}',
            amount=-cost,
            balance_after=user.coins,
            related_object_id=item_id,
            related_object_type=item_type,
            description=f'Spent on {item_type}'
        )
        
        return Response({
            'success': True,
            'message': 'Coins spent successfully',
            'new_balance': user.coins,
            'transaction': CoinTransactionSerializer(transaction).data
        })
    
    @action(detail=False, methods=['get'])
    def levels(self, request):
        """
        Get level information and progress
        GET /api/rewards/levels/
        """
        user = request.user
        
        level_thresholds = {
            1: {'name': 'Beginner', 'min': 0, 'max': 500},
            2: {'name': 'Growing', 'min': 501, 'max': 1500},
            3: {'name': 'Strong', 'min': 1501, 'max': 3000},
            4: {'name': 'Unbreakable', 'min': 3001, 'max': None}
        }
        
        current_level_info = level_thresholds[user.current_level]
        
        # Calculate progress to next level
        if current_level_info['max']:
            progress = ((user.total_points - current_level_info['min']) / 
                       (current_level_info['max'] - current_level_info['min'])) * 100
            points_to_next = current_level_info['max'] - user.total_points
            next_level = user.current_level + 1
        else:
            progress = 100
            points_to_next = 0
            next_level = None
        
        return Response({
            'success': True,
            'current_level': user.current_level,
            'level_name': current_level_info['name'],
            'total_points': user.total_points,
            'progress_percentage': round(progress, 2),
            'points_to_next_level': points_to_next,
            'next_level': next_level,
            'all_levels': level_thresholds
        })
    
    @action(detail=False, methods=['post'], url_path='claim-daily-bonus')
    def claim_daily_bonus(self, request):
        """
        Claim daily login bonus
        POST /api/rewards/claim-daily-bonus/
        """
        user = request.user
        today = timezone.now().date()
        
        # Check if already claimed today
        already_claimed = CoinTransaction.objects.filter(
            user=user,
            transaction_type='earned_daily_bonus',
            created_at__date=today
        ).exists()
        
        if already_claimed:
            return Response({
                'success': False,
                'message': 'Daily bonus already claimed today'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Award bonus
        bonus_coins = 5
        user.coins += bonus_coins
        user.save()
        
        # Create transaction
        transaction = CoinTransaction.objects.create(
            user=user,
            transaction_type='earned_daily_bonus',
            amount=bonus_coins,
            balance_after=user.coins,
            description='Daily login bonus'
        )
        
        return Response({
            'success': True,
            'message': 'Daily bonus claimed',
            'coins_earned': bonus_coins,
            'new_balance': user.coins,
            'transaction': CoinTransactionSerializer(transaction).data
        })


# ============================================
# PARTNER VIEWSET
# ============================================

class PartnerViewSet(viewsets.GenericViewSet):
    """
    ViewSet for partner interactions
    Endpoints: status, activity-status, notifications
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get partner's status
        GET /api/partner/status/
        """
        user = request.user
        
        if not user.partner:
            return Response({
                'success': False,
                'message': 'No partner linked',
                'has_partner': False
            })
        
        partner = user.partner
        today = timezone.now().date()
        
        # Partner's current activity
        current_activity = ActivitySession.objects.filter(
            user=partner,
            status__in=['started', 'in_progress']
        ).select_related('activity').first()
        
        current_activity_title = current_activity.activity.title_en if current_activity else None
        
        # Activities completed today
        activities_today = ActivityCompletion.objects.filter(
            user=partner,
            completed_at__date=today
        ).count()
        
        # Current streak
        partner_streak = partner.get_current_streak()
        
        data = {
            'has_partner': True,
            'partner': {
                'id': str(partner.id),
                'username': partner.username,
                'profile_picture': partner.profile_picture,
                'current_level': partner.current_level,
                'total_points': partner.total_points
            },
            'is_online': partner.is_online,
            'last_active': partner.last_active,
            'current_activity': current_activity_title,
            'activities_completed_today': activities_today,
            'current_streak': partner_streak
        }
        
        return Response({
            'success': True,
            **data
        })
    
    @action(detail=False, methods=['get'], url_path='activity-status')
    def activity_status(self, request):
        """
        Check partner's activity status for a specific activity
        GET /api/partner/activity-status/?activity_id=uuid
        """
        if not request.user.partner:
            return Response({
                'success': False,
                'message': 'No partner linked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        activity_id = request.query_params.get('activity_id')
        if not activity_id:
            return Response({
                'success': False,
                'message': 'activity_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Activity not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        partner = request.user.partner
        today = timezone.now().date()
        
        # Check completion
        completion = ActivityCompletion.objects.filter(
            user=partner,
            activity=activity,
            completed_at__date=today
        ).first()
        
        # Check in progress
        in_progress = ActivitySession.objects.filter(
            user=partner,
            activity=activity,
            status__in=['started', 'in_progress']
        ).exists()
        
        return Response({
            'success': True,
            'activity_id': activity_id,
            'activity_title': activity.title_en,
            'partner_completed': completion is not None,
            'partner_in_progress': in_progress,
            'completed_at': completion.completed_at if completion else None
        })
    
    @action(detail=False, methods=['get'])
    def notifications(self, request):
        """
        Get partner-related notifications
        GET /api/partner/notifications/
        """
        notifications = Notification.objects.filter(
            user=request.user,
            notification_type='partner_activity'
        )[:20]
        
        serializer = NotificationSerializer(
            notifications,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'notifications': serializer.data
        })


# ============================================
# NOTIFICATION VIEWSET
# ============================================

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for notifications
    Endpoints: list, retrieve, mark-read, mark-all-read, unread-count
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        List all notifications
        GET /api/notifications/
        Query params: ?unread_only=true&limit=20
        """
        queryset = self.get_queryset()
        
        # Filter unread only
        if request.query_params.get('unread_only', '').lower() == 'true':
            queryset = queryset.filter(is_read=False)
        
        # Limit
        limit = int(request.query_params.get('limit', 20))
        queryset = queryset[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'notifications': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """
        Mark a notification as read
        POST /api/notifications/{id}/mark-read/
        """
        notification = self.get_object()
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Mark all notifications as read
        POST /api/notifications/mark-all-read/
        """
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'{updated} notifications marked as read',
            'count': updated
        })
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Get unread notification count
        GET /api/notifications/unread-count/
        """
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({
            'success': True,
            'unread_count': count
        })


# ============================================
# SETTINGS VIEWSET
# ============================================
class SettingsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for app settings
    Endpoints: get-settings, update-settings
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserPreferenceSerializer
    
    @action(detail=False, methods=['get'], url_path='get-settings')
    def get_settings(self, request):  # ✅ Renamed from 'get'
        """
        Get all user settings
        GET /api/settings/get-settings/
        """
        user = request.user
        preference, created = UserPreference.objects.get_or_create(user=user)
        
        settings_data = {
            'profile': {
                'username': user.username,
                'email': user.email,
                'preferred_language': user.preferred_language,
                'theme': user.theme
            },
            'notifications': UserPreferenceSerializer(preference).data,
            'account': {
                'has_partner': user.partner is not None,
                'invitation_code': user.partner_invitation_code,
                'relationship_start_date': user.relationship_start_date
            }
        }
        
        return Response({
            'success': True,
            'settings': settings_data
        })
    
    @action(detail=False, methods=['put', 'patch'], url_path='update-settings')
    def update_settings(self, request):  # ✅ Renamed from 'update'
        """
        Update settings
        PUT/PATCH /api/settings/update-settings/
        """
        user = request.user
        preference, created = UserPreference.objects.get_or_create(user=user)
        
        # Update user profile settings
        profile_data = request.data.get('profile', {})
        for key in ['preferred_language', 'theme']:
            if key in profile_data:
                setattr(user, key, profile_data[key])
        user.save()
        
        # Update notification preferences
        notification_data = request.data.get('notifications', {})
        serializer = UserPreferenceSerializer(
            preference,
            data=notification_data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Settings updated successfully'
        })
        
        
# class SettingsViewSet(viewsets.GenericViewSet):
    # """
    # ViewSet for app settings
    # Endpoints: get, update
    # """
    # permission_classes = [IsAuthenticated]
    # serializer_class = UserPreferenceSerializer
    
    # @action(detail=False, methods=['get'])
    # def get(self, request):
    #     """
    #     Get all user settings
    #     GET /api/settings/
    #     """
    #     user = request.user
    #     preference, created = UserPreference.objects.get_or_create(user=user)
        
    #     settings_data = {
    #         'profile': {
    #             'username': user.username,
    #             'email': user.email,
    #             'preferred_language': user.preferred_language,
    #             'theme': user.theme
    #         },
    #         'notifications': UserPreferenceSerializer(preference).data,
    #         'account': {
    #             'has_partner': user.partner is not None,
    #             'invitation_code': user.partner_invitation_code,
    #             'relationship_start_date': user.relationship_start_date
    #         }
    #     }
        
    #     return Response({
    #         'success': True,
    #         'settings': settings_data
    #     })
    
    # @action(detail=False, methods=['put', 'patch'])
    # def update(self, request):
    #     """
    #     Update settings
    #     PUT/PATCH /api/settings/
    #     """
    #     user = request.user
    #     preference, created = UserPreference.objects.get_or_create(user=user)
        
    #     # Update user profile settings
    #     profile_data = request.data.get('profile', {})
    #     for key in ['preferred_language', 'theme']:
    #         if key in profile_data:
    #             setattr(user, key, profile_data[key])
    #     user.save()
        
    #     # Update notification preferences
    #     notification_data = request.data.get('notifications', {})
    #     serializer = UserPreferenceSerializer(
    #         preference,
    #         data=notification_data,
    #         partial=True
    #     )
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
        
    #     return Response({
    #         'success': True,
    #         'message': 'Settings updated successfully'
    #     })
        
        
def index(request):
    return render(request, 'home/index.html')