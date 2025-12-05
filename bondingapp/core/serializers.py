"""
DRF Serializers for Bonding App
Location: bondingapp/core/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from bondingapp.models import (
    User, UserPreference, ActivityCategory, Activity, 
    ActivitySession, ActivityCompletion, Streak, Badge, 
    UserBadge, Milestone, UserMilestone, Notification, 
    SkipLimit, CoinTransaction
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


# ============================================
# USER & AUTHENTICATION SERIALIZERS
# ============================================

class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user preferences and notification settings"""
    
    class Meta:
        model = UserPreference
        exclude = ['user', 'created_at', 'updated_at']
        

class PartnerBasicSerializer(serializers.ModelSerializer):
    """Basic partner information for nested serialization"""
    
    is_online = serializers.BooleanField(read_only=True)
    last_active = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'profile_picture', 
            'is_online', 'last_active', 'current_level', 'total_points'
        ]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Complete user profile serializer"""
    
    partner = PartnerBasicSerializer(read_only=True)
    preferences = UserPreferenceSerializer(read_only=True)
    bond_score = serializers.SerializerMethodField()
    current_streak = serializers.SerializerMethodField()
    relationship_duration_days = serializers.SerializerMethodField()
    level_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'age', 'profile_picture', 'bio', 'phone_number',
            'partner', 'relationship_start_date', 'partner_invitation_code',
            'preferred_language', 'theme', 'total_points', 'current_level', 'coins',
            'is_online', 'last_active', 'created_at',
            'bond_score', 'current_streak', 'relationship_duration_days',
            'level_progress', 'preferences'
        ]
        read_only_fields = [
            'id', 'email', 'partner', 'partner_invitation_code',
            'total_points', 'current_level', 'coins', 'is_online',
            'last_active', 'created_at', 'bond_score', 'current_streak',
            'relationship_duration_days', 'level_progress'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'phone_number': {'required': False},
        }
    
    def get_bond_score(self, obj):
        """Calculate and return bond score"""
        return obj.calculate_bond_score()
    
    def get_current_streak(self, obj):
        """Get current activity streak"""
        return obj.get_current_streak()
    
    def get_relationship_duration_days(self, obj):
        """Calculate relationship duration in days"""
        if obj.relationship_start_date:
            delta = timezone.now().date() - obj.relationship_start_date
            return delta.days
        return 0
    
    def get_level_progress(self, obj):
        """Calculate progress to next level"""
        level_thresholds = {
            1: (0, 500),
            2: (501, 1500),
            3: (1501, 3000),
            4: (3001, float('inf'))
        }
        
        current_threshold = level_thresholds.get(obj.current_level, (0, 500))
        if current_threshold[1] == float('inf'):
            return {
                'current_level': obj.current_level,
                'next_level': None,
                'progress_percentage': 100,
                'points_needed': 0
            }
        
        points_in_level = obj.total_points - current_threshold[0]
        level_range = current_threshold[1] - current_threshold[0]
        progress_percentage = (points_in_level / level_range) * 100
        
        return {
            'current_level': obj.current_level,
            'next_level': obj.current_level + 1,
            'progress_percentage': round(progress_percentage, 2),
            'points_needed': current_threshold[1] - obj.total_points
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'age', 'preferred_language'
        ]
    
    def validate(self, data):
        """Validate registration data"""
        if 'password' in data:
            if data.get('password') != data.get('confirm_password'):
                raise serializers.ValidationError({
                    "password": "Passwords don't match."
                })
        return data
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        
        # Create default preferences
        UserPreference.objects.create(user=user)
        
        # Generate invitation code
        user.generate_invitation_code()
        
        return user


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth authentication"""
    
    google_token = serializers.CharField(required=True)
    
    def validate_google_token(self, value):
        """Validate Google token (implement token verification)"""
        if not value:
            raise serializers.ValidationError("Google token is required")
        return value

class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    

class PartnerLinkSerializer(serializers.Serializer):
    """Serializer for partner linking"""
    
    invitation_code = serializers.CharField(max_length=8, required=True)
    
    def validate_invitation_code(self, value):
        """Validate invitation code exists"""
        if not User.objects.filter(partner_invitation_code=value).exists():
            raise serializers.ValidationError("Invalid invitation code")
        return value.upper()


# ============================================
# ACTIVITY SERIALIZERS
# ============================================

class ActivityCategorySerializer(serializers.ModelSerializer):
    """Serializer for activity categories"""
    
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityCategory
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'display_order', 'activity_count', 'is_active'
        ]
    
    def get_name(self, obj):
        """Get localized name based on user preference"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.preferred_language == 'hi':
            return obj.name_hi
        return obj.name_en
    
    def get_description(self, obj):
        """Get localized description"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.preferred_language == 'hi':
            return obj.description_hi
        return obj.description_en
    
    def get_activity_count(self, obj):
        """Count active activities in this category"""
        return obj.activities.filter(is_active=True).count()


class ActivityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for activity listing"""
    
    category = ActivityCategorySerializer(read_only=True)
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_completed_today = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'category', 'title', 'description', 'difficulty',
            'estimated_time_minutes', 'best_time', 'mode', 'is_premium',
            'unlock_cost_coins', 'points_reward', 'coins_reward',
            'completion_count', 'average_rating', 'is_daily_featured',
            'is_completed_today', 'is_unlocked'
        ]
    
    def get_title(self, obj):
        """Get localized title"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.preferred_language == 'hi':
            return obj.title_hi
        return obj.title_en
    
    def get_description(self, obj):
        """Get localized description"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.preferred_language == 'hi':
            return obj.description_hi
        return obj.description_en
    
    def get_is_completed_today(self, obj):
        """Check if user completed this activity today"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            today = timezone.now().date()
            return ActivityCompletion.objects.filter(
                user=user,
                activity=obj,
                completed_at__date=today
            ).exists()
        return False
    
    def get_is_unlocked(self, obj):
        """Check if premium activity is unlocked"""
        if not obj.is_premium:
            return True
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            # Check if user has completed this premium activity before (means it's unlocked)
            return ActivityCompletion.objects.filter(user=user, activity=obj).exists()
        return False


class ActivityDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single activity view"""
    
    category = ActivityCategorySerializer(read_only=True)
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    materials_needed = serializers.SerializerMethodField()
    tips = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    is_completed_today = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()
    partner_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'category', 'title', 'description', 'instructions',
            'difficulty', 'estimated_time_minutes', 'best_time', 'mode',
            'materials_needed', 'tips', 'questions', 'points_reward',
            'coins_reward', 'is_premium', 'unlock_cost_coins',
            'completion_count', 'average_rating', 'is_daily_featured',
            'is_completed_today', 'is_unlocked', 'partner_status'
        ]
    
    def get_title(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.title_hi if user and user.preferred_language == 'hi' else obj.title_en
    
    def get_description(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.description_hi if user and user.preferred_language == 'hi' else obj.description_en
    
    def get_instructions(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.instructions_hi if user and user.preferred_language == 'hi' else obj.instructions_en
    
    def get_materials_needed(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.materials_needed_hi if user and user.preferred_language == 'hi' else obj.materials_needed_en
    
    def get_tips(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.tips_hi if user and user.preferred_language == 'hi' else obj.tips_en
    
    def get_questions(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.questions_hi if user and user.preferred_language == 'hi' else obj.questions_en
    
    def get_is_completed_today(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            today = timezone.now().date()
            return ActivityCompletion.objects.filter(
                user=user, activity=obj, completed_at__date=today
            ).exists()
        return False
    
    def get_is_unlocked(self, obj):
        if not obj.is_premium:
            return True
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            return ActivityCompletion.objects.filter(user=user, activity=obj).exists()
        return False
    
    def get_partner_status(self, obj):
        """Get partner's activity status"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.partner:
            today = timezone.now().date()
            partner_completed = ActivityCompletion.objects.filter(
                user=user.partner,
                activity=obj,
                completed_at__date=today
            ).exists()
            
            partner_in_progress = ActivitySession.objects.filter(
                user=user.partner,
                activity=obj,
                status__in=['started', 'in_progress']
            ).exists()
            
            return {
                'completed': partner_completed,
                'in_progress': partner_in_progress
            }
        return None


# ============================================
# ACTIVITY SESSION & COMPLETION SERIALIZERS
# ============================================

class ActivitySessionSerializer(serializers.ModelSerializer):
    """Serializer for activity sessions"""
    
    activity = ActivityListSerializer(read_only=True)
    activity_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = ActivitySession
        fields = [
            'id', 'activity', 'activity_id', 'status', 'mode',
            'started_at', 'completed_at', 'time_spent_seconds'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'time_spent_seconds']
    
    def create(self, validated_data):
        """Create activity session"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ActivityCompletionSerializer(serializers.ModelSerializer):
    """Serializer for activity completions"""
    
    activity = ActivityListSerializer(read_only=True)
    session_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = ActivityCompletion
        fields = [
            'id', 'activity', 'session_id', 'responses', 'photos', 'notes',
            'rating', 'feedback', 'points_earned', 'coins_earned',
            'shared_with_partner', 'completed_at'
        ]
        read_only_fields = ['id', 'points_earned', 'coins_earned', 'completed_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        """Create activity completion and update user stats"""
        session_id = validated_data.pop('session_id')
        
        try:
            session = ActivitySession.objects.get(
                id=session_id,
                user=self.context['request'].user
            )
        except ActivitySession.DoesNotExist:
            raise serializers.ValidationError({"session_id": "Invalid session ID"})
        
        # Set rewards
        validated_data['user'] = self.context['request'].user
        validated_data['activity'] = session.activity
        validated_data['session'] = session
        validated_data['points_earned'] = session.activity.points_reward
        validated_data['coins_earned'] = session.activity.coins_reward
        
        # Create completion
        completion = super().create(validated_data)
        
        # Update session status
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        # Update user stats
        user = self.context['request'].user
        user.total_points += completion.points_earned
        user.coins += completion.coins_earned
        
        # Update level
        if user.total_points >= 3001:
            user.current_level = 4
        elif user.total_points >= 1501:
            user.current_level = 3
        elif user.total_points >= 501:
            user.current_level = 2
        else:
            user.current_level = 1
        
        user.save()
        
        # Update streak
        streak, created = Streak.objects.get_or_create(user=user)
        streak.update_streak()
        
        # Create coin transaction
        CoinTransaction.objects.create(
            user=user,
            transaction_type='earned_activity',
            amount=completion.coins_earned,
            balance_after=user.coins,
            related_object_id=completion.activity.id,
            related_object_type='activity',
            description=f"Earned from completing {completion.activity.title_en}"
        )
        
        return completion


class ActivityCompletionHistorySerializer(serializers.ModelSerializer):
    """Serializer for viewing completion history"""
    
    activity = ActivityListSerializer(read_only=True)
    
    class Meta:
        model = ActivityCompletion
        fields = [
            'id', 'activity', 'responses', 'photos', 'notes',
            'rating', 'points_earned', 'coins_earned', 'completed_at'
        ]


# ============================================
# GAMIFICATION SERIALIZERS
# ============================================

class StreakSerializer(serializers.ModelSerializer):
    """Serializer for user streaks"""
    
    is_active = serializers.SerializerMethodField()
    days_until_break = serializers.SerializerMethodField()
    
    class Meta:
        model = Streak
        fields = [
            'current_streak', 'longest_streak', 'last_activity_date',
            'total_active_days', 'streak_start_date', 'is_active',
            'days_until_break'
        ]
    
    def get_is_active(self, obj):
        """Check if streak is active"""
        return obj.is_active()
    
    def get_days_until_break(self, obj):
        """Calculate days until streak breaks"""
        if not obj.last_activity_date:
            return 0
        
        today = timezone.now().date()
        days_since = (today - obj.last_activity_date).days
        
        if days_since >= 1:
            return 0  # Streak will break today
        return 1  # Have until tomorrow


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for badges"""
    
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'icon', 'category',
            'criteria', 'points_reward', 'coins_reward', 'rarity',
            'is_unlocked'
        ]
    
    def get_name(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.name_hi if user and user.preferred_language == 'hi' else obj.name_en
    
    def get_description(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.description_hi if user and user.preferred_language == 'hi' else obj.description_en
    
    def get_is_unlocked(self, obj):
        """Check if user has unlocked this badge"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            return UserBadge.objects.filter(user=user, badge=obj).exists()
        return False


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for user unlocked badges"""
    
    badge = BadgeSerializer(read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'unlocked_at', 'is_displayed']


class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for milestones"""
    
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_achieved = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Milestone
        fields = [
            'id', 'name', 'description', 'icon', 'milestone_type',
            'criteria_value', 'points_reward', 'coins_reward',
            'is_achieved', 'progress'
        ]
    
    def get_name(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.name_hi if user and user.preferred_language == 'hi' else obj.name_en
    
    def get_description(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.description_hi if user and user.preferred_language == 'hi' else obj.description_en
    
    def get_is_achieved(self, obj):
        """Check if user has achieved this milestone"""
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            return UserMilestone.objects.filter(user=user, milestone=obj).exists()
        return False
    
    def get_progress(self, obj):
        """Calculate progress towards milestone"""
        user = self.context.get('request').user if self.context.get('request') else None
        if not user:
            return 0
        
        if obj.milestone_type == 'activity_count':
            current_value = ActivityCompletion.objects.filter(user=user).count()
        elif obj.milestone_type == 'streak':
            streak = Streak.objects.filter(user=user).first()
            current_value = streak.longest_streak if streak else 0
        elif obj.milestone_type == 'relationship_duration':
            if user.relationship_start_date:
                delta = timezone.now().date() - user.relationship_start_date
                current_value = delta.days
            else:
                current_value = 0
        else:
            current_value = 0
        
        progress_percentage = (current_value / obj.criteria_value) * 100
        return min(progress_percentage, 100)


class UserMilestoneSerializer(serializers.ModelSerializer):
    """Serializer for achieved milestones"""
    
    milestone = MilestoneSerializer(read_only=True)
    
    class Meta:
        model = UserMilestone
        fields = ['id', 'milestone', 'achieved_at', 'partner_also_achieved']


class CoinTransactionSerializer(serializers.ModelSerializer):
    """Serializer for coin transactions"""
    
    class Meta:
        model = CoinTransaction
        fields = [
            'id', 'transaction_type', 'amount', 'balance_after',
            'description', 'created_at'
        ]


class CoinSpendSerializer(serializers.Serializer):
    """Serializer for spending coins"""
    
    item_type = serializers.ChoiceField(choices=[
        'unlock_activity', 'hint', 'theme', 'custom_activity'
    ])
    item_id = serializers.UUIDField(required=False)
    cost = serializers.IntegerField(min_value=1)
    
    def validate(self, data):
        """Validate coin spending"""
        user = self.context['request'].user
        
        if user.coins < data['cost']:
            raise serializers.ValidationError("Insufficient coins")
        
        return data


# ============================================
# PROGRESS & STATS SERIALIZERS
# ============================================

class ProgressOverviewSerializer(serializers.Serializer):
    """Serializer for overall progress overview"""
    
    total_activities_completed = serializers.IntegerField()
    activities_this_week = serializers.IntegerField()
    activities_this_month = serializers.IntegerField()
    bond_score = serializers.IntegerField()
    bond_score_change = serializers.FloatField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    total_points = serializers.IntegerField()
    total_coins = serializers.IntegerField()
    current_level = serializers.IntegerField()
    badges_unlocked = serializers.IntegerField()
    milestones_achieved = serializers.IntegerField()
    favorite_category = serializers.CharField()
    most_active_day = serializers.CharField()
    partner_sync_rate = serializers.FloatField()


class BondScoreHistorySerializer(serializers.Serializer):
    """Serializer for bond score history"""
    
    date = serializers.DateField()
    score = serializers.IntegerField()


# ============================================
# NOTIFICATION SERIALIZERS
# ============================================

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    
    title = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'data',
            'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def get_title(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.title_hi if user and user.preferred_language == 'hi' else obj.title_en
    
    def get_message(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        return obj.message_hi if user and user.preferred_language == 'hi' else obj.message_en


# ============================================
# PARTNER INTERACTION SERIALIZERS
# ============================================

class PartnerStatusSerializer(serializers.Serializer):
    """Serializer for partner status"""
    
    partner = PartnerBasicSerializer()
    is_online = serializers.BooleanField()
    last_active = serializers.DateTimeField()
    current_activity = serializers.CharField(allow_null=True)
    activities_completed_today = serializers.IntegerField()
    current_streak = serializers.IntegerField()


class PartnerActivityStatusSerializer(serializers.Serializer):
    """Serializer for partner activity status"""
    
    activity_id = serializers.UUIDField()
    activity_title = serializers.CharField()
    partner_completed = serializers.BooleanField()
    partner_in_progress = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)