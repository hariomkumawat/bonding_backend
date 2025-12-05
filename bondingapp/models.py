from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid


class User(AbstractUser):
    """Extended User model with relationship features"""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    
    # Profile fields
    age = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(13), MaxValueValidator(120)])
    profile_picture = models.URLField(null=True, blank=True)
    bio = models.TextField(max_length=500, null=True, blank=True)
    
    # Relationship fields
    partner = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='partner_of')
    relationship_start_date = models.DateField(null=True, blank=True)
    partner_invitation_code = models.CharField(max_length=8, unique=True, null=True, blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='auto')
    
    # Activity tracking
    total_points = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    coins = models.IntegerField(default=0)
    
    # Timestamps
    last_active = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['google_id']),
            models.Index(fields=['partner_invitation_code']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def generate_invitation_code(self):
        """Generate unique 8-character invitation code"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not User.objects.filter(partner_invitation_code=code).exists():
                self.partner_invitation_code = code
                self.save()
                return code
    
    def calculate_bond_score(self):
        """Calculate bond score based on activities completed"""
        if not self.partner:
            return 0
        
        # Get activities completed by both partners in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        user_completions = self.activity_completions.filter(completed_at__gte=thirty_days_ago).count()
        partner_completions = self.partner.activity_completions.filter(completed_at__gte=thirty_days_ago).count()
        
        # Get streak
        streak = self.get_current_streak()
        
        # Calculate score (out of 100)
        base_score = min((user_completions + partner_completions) * 2, 60)  # Max 60 from activities
        streak_score = min(streak * 2, 30)  # Max 30 from streak
        consistency_score = 10 if user_completions >= 20 and partner_completions >= 20 else 5
        
        return min(base_score + streak_score + consistency_score, 100)
    
    def get_current_streak(self):
        """Calculate current activity streak"""
        streak_obj = self.streaks.first()
        if streak_obj and streak_obj.is_active():
            return streak_obj.current_streak
        return 0


class UserPreference(models.Model):
    """User app preferences and notification settings"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences
    daily_reminder_enabled = models.BooleanField(default=True)
    daily_reminder_time = models.TimeField(default='09:00:00')
    partner_activity_alerts = models.BooleanField(default=True)
    streak_reminders = models.BooleanField(default=True)
    milestone_notifications = models.BooleanField(default=True)
    
    # Sound & Vibration
    sound_enabled = models.BooleanField(default=True)
    vibration_enabled = models.BooleanField(default=True)
    
    # Activity preferences
    activity_difficulty = models.CharField(
        max_length=10,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('deep', 'Deep'), ('all', 'All')],
        default='all'
    )
    notification_frequency = models.CharField(
        max_length=10,
        choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='medium'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class ActivityCategory(models.Model):
    """Categories for organizing activities"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_en = models.CharField(max_length=100)
    name_hi = models.CharField(max_length=100)
    description_en = models.TextField()
    description_hi = models.TextField()
    icon = models.CharField(max_length=50)  # Emoji or icon name
    color = models.CharField(max_length=7, default='#FFB6C1')  # Hex color
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activity_categories'
        ordering = ['display_order', 'name_en']
        verbose_name_plural = 'Activity Categories'
    
    def __str__(self):
        return f"{self.icon} {self.name_en}"


class Activity(models.Model):
    """Activity templates that users can complete"""
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('deep', 'Deep'),
    ]
    
    TIME_OF_DAY_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('anytime', 'Anytime'),
    ]
    
    MODE_CHOICES = [
        ('solo', 'Solo'),
        ('together', 'Together'),
        ('both', 'Both'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE, related_name='activities')
    
    # Content (bilingual)
    title_en = models.CharField(max_length=200)
    title_hi = models.CharField(max_length=200)
    description_en = models.TextField()
    description_hi = models.TextField()
    instructions_en = models.JSONField()  # Array of steps
    instructions_hi = models.JSONField()
    
    # Metadata
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    estimated_time_minutes = models.IntegerField(validators=[MinValueValidator(5), MaxValueValidator(120)])
    best_time = models.CharField(max_length=10, choices=TIME_OF_DAY_CHOICES, default='anytime')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='both')
    
    # Materials & Tips
    materials_needed_en = models.JSONField(null=True, blank=True)  # Array of items
    materials_needed_hi = models.JSONField(null=True, blank=True)
    tips_en = models.JSONField(null=True, blank=True)  # Array of tips
    tips_hi = models.JSONField(null=True, blank=True)
    
    # Questions/Prompts (if applicable)
    questions_en = models.JSONField(null=True, blank=True)  # Array of questions
    questions_hi = models.JSONField(null=True, blank=True)
    
    # Gamification
    points_reward = models.IntegerField(default=10)
    coins_reward = models.IntegerField(default=10)
    
    # Premium feature
    is_premium = models.BooleanField(default=False)
    unlock_cost_coins = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_daily_featured = models.BooleanField(default=False)
    
    # Analytics
    completion_count = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activities'
        indexes = [
            models.Index(fields=['category', 'difficulty']),
            models.Index(fields=['is_daily_featured']),
            models.Index(fields=['is_premium']),
        ]
    
    def __str__(self):
        return f"{self.title_en} ({self.difficulty})"


class ActivitySession(models.Model):
    """Tracks when a user starts an activity"""
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('abandoned', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_sessions')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='sessions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    mode = models.CharField(max_length=10, choices=[('solo', 'Solo'), ('together', 'Together')], default='solo')
    
    # Partner session (if together mode)
    partner_session = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='linked_session')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'activity_sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity.title_en} ({self.status})"


class ActivityCompletion(models.Model):
    """Records completed activities with user responses"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_completions')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='completions')
    session = models.OneToOneField(ActivitySession, on_delete=models.CASCADE, related_name='completion')
    
    # Responses
    responses = models.JSONField(null=True, blank=True)  # Store Q&A or completion data
    photos = models.JSONField(null=True, blank=True)  # Array of photo URLs
    notes = models.TextField(null=True, blank=True)
    
    # Ratings & Feedback
    rating = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    feedback = models.TextField(null=True, blank=True)
    
    # Rewards earned
    points_earned = models.IntegerField(default=10)
    coins_earned = models.IntegerField(default=10)
    
    # Visibility
    shared_with_partner = models.BooleanField(default=True)
    
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_completions'
        indexes = [
            models.Index(fields=['user', 'completed_at']),
            models.Index(fields=['activity']),
        ]
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.username} completed {self.activity.title_en}"


class Streak(models.Model):
    """Tracks user's daily activity streak"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streaks')
    
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    total_active_days = models.IntegerField(default=0)
    streak_start_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'streaks'
        ordering = ['-current_streak']
    
    def __str__(self):
        return f"{self.user.username} - {self.current_streak} days streak"
    
    def is_active(self):
        """Check if streak is still active (activity within last 24 hours)"""
        if not self.last_activity_date:
            return False
        days_since = (timezone.now().date() - self.last_activity_date).days
        return days_since <= 1
    
    def update_streak(self):
        """Update streak when user completes an activity"""
        today = timezone.now().date()
        
        if not self.last_activity_date:
            # First activity
            self.current_streak = 1
            self.longest_streak = 1
            self.last_activity_date = today
            self.streak_start_date = today
            self.total_active_days = 1
        elif self.last_activity_date == today:
            # Already completed activity today
            return
        elif (today - self.last_activity_date).days == 1:
            # Consecutive day
            self.current_streak += 1
            self.longest_streak = max(self.longest_streak, self.current_streak)
            self.last_activity_date = today
            self.total_active_days += 1
        else:
            # Streak broken
            self.current_streak = 1
            self.last_activity_date = today
            self.streak_start_date = today
            self.total_active_days += 1
        
        self.save()


class Badge(models.Model):
    """Achievement badges users can unlock"""
    
    CATEGORY_CHOICES = [
        ('streak', 'Streak'),
        ('completion', 'Completion'),
        ('category', 'Category'),
        ('special', 'Special'),
        ('milestone', 'Milestone'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Badge details (bilingual)
    name_en = models.CharField(max_length=100)
    name_hi = models.CharField(max_length=100)
    description_en = models.TextField()
    description_hi = models.TextField()
    
    icon = models.CharField(max_length=100)  # Emoji or icon identifier
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Unlock criteria
    criteria = models.JSONField()  # e.g., {"type": "streak", "value": 7}
    points_reward = models.IntegerField(default=50)
    coins_reward = models.IntegerField(default=20)
    
    # Display
    rarity = models.CharField(
        max_length=10,
        choices=[('common', 'Common'), ('rare', 'Rare'), ('epic', 'Epic'), ('legendary', 'Legendary')],
        default='common'
    )
    display_order = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'badges'
        ordering = ['display_order', 'name_en']
    
    def __str__(self):
        return f"{self.icon} {self.name_en}"


class UserBadge(models.Model):
    """Badges unlocked by users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    
    unlocked_at = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=False)  # Show on profile
    
    class Meta:
        db_table = 'user_badges'
        unique_together = ['user', 'badge']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name_en}"


class Milestone(models.Model):
    """Relationship milestones to celebrate"""
    
    MILESTONE_TYPE_CHOICES = [
        ('relationship_duration', 'Relationship Duration'),
        ('activity_count', 'Activity Count'),
        ('streak', 'Streak'),
        ('special', 'Special Event'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Milestone details (bilingual)
    name_en = models.CharField(max_length=100)
    name_hi = models.CharField(max_length=100)
    description_en = models.TextField()
    description_hi = models.TextField()
    
    icon = models.CharField(max_length=50)
    milestone_type = models.CharField(max_length=30, choices=MILESTONE_TYPE_CHOICES)
    
    # Criteria
    criteria_value = models.IntegerField()  # e.g., 30 for 30 days, 100 for 100 activities
    points_reward = models.IntegerField(default=100)
    coins_reward = models.IntegerField(default=50)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'milestones'
    
    def __str__(self):
        return f"{self.icon} {self.name_en}"


class UserMilestone(models.Model):
    """Milestones achieved by users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achieved_milestones')
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='user_milestones')
    
    achieved_at = models.DateTimeField(auto_now_add=True)
    partner_also_achieved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_milestones'
        unique_together = ['user', 'milestone']
        ordering = ['-achieved_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.milestone.name_en}"


class Notification(models.Model):
    """In-app notifications for users"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('partner_activity', 'Partner Activity'),
        ('streak_reminder', 'Streak Reminder'),
        ('daily_activity', 'Daily Activity'),
        ('badge_unlocked', 'Badge Unlocked'),
        ('milestone_achieved', 'Milestone Achieved'),
        ('partner_invite', 'Partner Invitation'),
        ('partner_joined', 'Partner Joined'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    
    # Content (bilingual)
    title_en = models.CharField(max_length=200)
    title_hi = models.CharField(max_length=200)
    message_en = models.TextField()
    message_hi = models.TextField()
    
    # Metadata
    data = models.JSONField(null=True, blank=True)  # Additional data (activity_id, badge_id, etc.)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)  # For push notifications
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"


class SkipLimit(models.Model):
    """Track daily skip limits for users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skip_limits')
    date = models.DateField(default=timezone.now)
    skips_used = models.IntegerField(default=0)
    max_skips_per_day = models.IntegerField(default=2)
    
    class Meta:
        db_table = 'skip_limits'
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.skips_used}/{self.max_skips_per_day}"
    
    def can_skip(self):
        """Check if user can skip more activities today"""
        return self.skips_used < self.max_skips_per_day


class CoinTransaction(models.Model):
    """Track all coin transactions for transparency"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('earned_activity', 'Earned from Activity'),
        ('earned_daily_bonus', 'Daily Login Bonus'),
        ('earned_streak', 'Streak Bonus'),
        ('earned_badge', 'Badge Reward'),
        ('earned_milestone', 'Milestone Reward'),
        ('spent_unlock', 'Spent to Unlock'),
        ('spent_hint', 'Spent on Hint'),
        ('spent_theme', 'Spent on Theme'),
        ('spent_custom', 'Spent on Custom Activity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coin_transactions')
    
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.IntegerField()  # Positive for earning, negative for spending
    balance_after = models.IntegerField()
    
    # Reference to related object
    related_object_id = models.UUIDField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)  # activity, badge, etc.
    
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'coin_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} ({self.amount} coins)"