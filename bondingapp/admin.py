"""
Django Admin Configuration with Import/Export
Location: bondingapp/admin.py
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from bondingapp.models import (
    User, UserPreference, ActivityCategory, Activity,
    ActivitySession, ActivityCompletion, Streak, Badge,
    UserBadge, Milestone, UserMilestone, Notification,
    SkipLimit, CoinTransaction
)

import json
from import_export import resources, fields, widgets
from import_export.admin import ImportExportModelAdmin
from bondingapp.models import Activity, ActivityCategory

# ============================================
# RESOURCES (Define what/how to import/export)
# ============================================

class UserResource(resources.ModelResource):
    """Resource for User model import/export"""
    partner = fields.Field(
        column_name='partner',
        attribute='partner',
        widget=ForeignKeyWidget(User, 'email')
    )
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'age', 'phone_number', 'partner', 'relationship_start_date',
            'preferred_language', 'theme', 'total_points', 'current_level',
            'coins', 'is_active', 'created_at'
        )
        export_order = fields
        import_id_fields = ['email']  # Use email as unique identifier for imports
        skip_unchanged = True
        report_skipped = True


class ActivityCategoryResource(resources.ModelResource):
    """Resource for ActivityCategory import/export"""
    
    class Meta:
        model = ActivityCategory
        fields = (
            'id', 'name_en', 'name_hi', 'description_en', 'description_hi',
            'icon', 'color', 'display_order', 'is_active'
        )
        export_order = fields
        import_id_fields = ['name_en']


class ActivityResource(resources.ModelResource):
    """Resource for Activity import/export"""
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(ActivityCategory, 'name_en')
    )
    
    class Meta:
        model = Activity
        fields = (
            'id', 'category', 'title_en', 'title_hi', 'description_en',
            'description_hi', 'difficulty', 'estimated_time_minutes',
            'best_time', 'mode', 'points_reward', 'coins_reward',
            'is_premium', 'unlock_cost_coins', 'is_active', 'is_daily_featured'
        )
        export_order = fields


class ActivityCompletionResource(resources.ModelResource):
    """Resource for ActivityCompletion import/export"""
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'email')
    )
    activity = fields.Field(
        column_name='activity',
        attribute='activity',
        widget=ForeignKeyWidget(Activity, 'title_en')
    )
    
    class Meta:
        model = ActivityCompletion
        fields = (
            'id', 'user', 'activity', 'rating', 'points_earned',
            'coins_earned', 'shared_with_partner', 'completed_at'
        )
        export_order = fields


class BadgeResource(resources.ModelResource):
    """Resource for Badge import/export"""
    
    class Meta:
        model = Badge
        fields = (
            'id', 'name_en', 'name_hi', 'description_en', 'description_hi',
            'icon', 'category', 'criteria', 'points_reward', 'coins_reward',
            'rarity', 'is_active'
        )
        export_order = fields


class CoinTransactionResource(resources.ModelResource):
    """Resource for CoinTransaction import/export"""
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'email')
    )
    
    class Meta:
        model = CoinTransaction
        fields = (
            'id', 'user', 'transaction_type', 'amount', 'balance_after',
            'description', 'created_at'
        )
        export_order = fields


# ============================================
# ADMIN CLASSES
# ============================================

@admin.register(User)
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    """Admin for User model with import/export"""
    resource_class = UserResource
    
    list_display = (
        'username', 'email', 'partner_link', 'current_level', 
        'total_points', 'coins', 'is_online', 'created_at'
    )
    list_filter = (
        'is_active', 'is_staff', 'current_level', 
        'preferred_language', 'theme', 'created_at'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Account', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'age', 'phone_number', 'profile_picture', 'bio')
        }),
        ('Relationship', {
            'fields': ('partner', 'relationship_start_date', 'partner_invitation_code')
        }),
        ('Preferences', {
            'fields': ('preferred_language', 'theme')
        }),
        ('Gamification', {
            'fields': ('total_points', 'current_level', 'coins')
        }),
        ('Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_online', 'last_active')
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('last_active', 'created_at', 'updated_at')
    
    def partner_link(self, obj):
        """Display partner as clickable link"""
        if obj.partner:
            url = reverse('admin:bondingapp_user_change', args=[obj.partner.id])
            return format_html('<a href="{}">{}</a>', url, obj.partner.username)
        return '-'
    partner_link.short_description = 'Partner'


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """Admin for UserPreference"""
    list_display = (
        'user', 'daily_reminder_enabled', 'daily_reminder_time',
        'partner_activity_alerts', 'activity_difficulty'
    )
    list_filter = (
        'daily_reminder_enabled', 'partner_activity_alerts',
        'streak_reminders', 'activity_difficulty'
    )
    search_fields = ('user__username', 'user__email')


@admin.register(ActivityCategory)
class ActivityCategoryAdmin(ImportExportModelAdmin):
    """Admin for ActivityCategory with import/export"""
    resource_class = ActivityCategoryResource
    
    list_display = (
        'icon_display', 'name_en', 'name_hi', 'color_display',
        'display_order', 'activity_count', 'is_active'
    )
    list_filter = ('is_active',)
    search_fields = ('name_en', 'name_hi')
    ordering = ('display_order', 'name_en')
    list_editable = ('display_order', 'is_active')
    
    def icon_display(self, obj):
        """Display icon emoji"""
        return obj.icon
    icon_display.short_description = 'Icon'
    
    def color_display(self, obj):
        """Display color swatch"""
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 3px; color: white;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def activity_count(self, obj):
        """Count activities in category"""
        return obj.activities.filter(is_active=True).count()
    activity_count.short_description = 'Activities'


# @admin.register(Activity)
class ActivityAdmin(ImportExportModelAdmin):
    """Admin for Activity with import/export"""
    resource_class = ActivityResource
    
    list_display = (
        'title_en', 'category', 'difficulty', 'estimated_time_minutes',
        'mode', 'points_reward', 'coins_reward', 'completion_count',
        'is_premium', 'is_daily_featured', 'is_active'
    )
    list_filter = (
        'category', 'difficulty', 'mode', 'best_time',
        'is_premium', 'is_daily_featured', 'is_active'
    )
    search_fields = ('title_en', 'title_hi', 'description_en', 'description_hi')
    ordering = ('-created_at',)
    list_editable = ('is_daily_featured', 'is_active')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('category', 'title_en', 'title_hi', 'description_en', 'description_hi')
        }),
        ('Instructions', {
            'fields': ('instructions_en', 'instructions_hi'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('difficulty', 'estimated_time_minutes', 'best_time', 'mode')
        }),
        ('Materials & Tips', {
            'fields': ('materials_needed_en', 'materials_needed_hi', 'tips_en', 'tips_hi'),
            'classes': ('collapse',)
        }),
        ('Questions', {
            'fields': ('questions_en', 'questions_hi'),
            'classes': ('collapse',)
        }),
        ('Gamification', {
            'fields': ('points_reward', 'coins_reward', 'is_premium', 'unlock_cost_coins')
        }),
        ('Status', {
            'fields': ('is_active', 'is_daily_featured', 'completion_count', 'average_rating')
        }),
    )
    
    readonly_fields = ('completion_count', 'average_rating', 'created_at', 'updated_at')


@admin.register(ActivitySession)
class ActivitySessionAdmin(admin.ModelAdmin):
    """Admin for ActivitySession"""
    list_display = (
        'user', 'activity', 'status', 'mode', 'started_at',
        'completed_at', 'time_spent_display'
    )
    list_filter = ('status', 'mode', 'started_at')
    search_fields = ('user__username', 'activity__title_en')
    readonly_fields = ('started_at', 'completed_at')
    
    def time_spent_display(self, obj):
        """Display time spent in readable format"""
        if obj.time_spent_seconds:
            minutes = obj.time_spent_seconds // 60
            seconds = obj.time_spent_seconds % 60
            return f"{minutes}m {seconds}s"
        return '-'
    time_spent_display.short_description = 'Time Spent'


@admin.register(ActivityCompletion)
class ActivityCompletionAdmin(ImportExportModelAdmin):
    """Admin for ActivityCompletion with import/export"""
    resource_class = ActivityCompletionResource
    
    list_display = (
        'user', 'activity', 'rating_display', 'points_earned',
        'coins_earned', 'shared_with_partner', 'completed_at'
    )
    list_filter = ('rating', 'shared_with_partner', 'completed_at')
    search_fields = ('user__username', 'activity__title_en')
    readonly_fields = ('completed_at',)
    date_hierarchy = 'completed_at'
    
    def rating_display(self, obj):
        """Display rating as stars"""
        if obj.rating:
            return '⭐' * obj.rating
        return '-'
    rating_display.short_description = 'Rating'


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    """Admin for Streak"""
    list_display = (
        'user', 'current_streak', 'longest_streak', 'last_activity_date',
        'total_active_days', 'is_active_display'
    )
    list_filter = ('last_activity_date',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
    
    def is_active_display(self, obj):
        """Display if streak is active"""
        return '✅' if obj.is_active() else '❌'
    is_active_display.short_description = 'Active'


@admin.register(Badge)
class BadgeAdmin(ImportExportModelAdmin):
    """Admin for Badge with import/export"""
    resource_class = BadgeResource
    
    list_display = (
        'icon_display', 'name_en', 'category', 'rarity',
        'points_reward', 'coins_reward', 'unlocked_count', 'is_active'
    )
    list_filter = ('category', 'rarity', 'is_active')
    search_fields = ('name_en', 'name_hi')
    ordering = ('display_order', 'name_en')
    
    def icon_display(self, obj):
        """Display badge icon"""
        return obj.icon
    icon_display.short_description = 'Icon'
    
    def unlocked_count(self, obj):
        """Count how many users unlocked this badge"""
        return UserBadge.objects.filter(badge=obj).count()
    unlocked_count.short_description = 'Unlocked By'


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """Admin for UserBadge"""
    list_display = ('user', 'badge', 'unlocked_at', 'is_displayed')
    list_filter = ('is_displayed', 'unlocked_at')
    search_fields = ('user__username', 'badge__name_en')
    readonly_fields = ('unlocked_at',)


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    """Admin for Milestone"""
    list_display = (
        'icon_display', 'name_en', 'milestone_type', 'criteria_value',
        'points_reward', 'coins_reward', 'achieved_count', 'is_active'
    )
    list_filter = ('milestone_type', 'is_active')
    search_fields = ('name_en', 'name_hi')
    
    def icon_display(self, obj):
        """Display milestone icon"""
        return obj.icon
    icon_display.short_description = 'Icon'
    
    def achieved_count(self, obj):
        """Count achievements"""
        return UserMilestone.objects.filter(milestone=obj).count()
    achieved_count.short_description = 'Achieved By'


@admin.register(UserMilestone)
class UserMilestoneAdmin(admin.ModelAdmin):
    """Admin for UserMilestone"""
    list_display = ('user', 'milestone', 'achieved_at', 'partner_also_achieved')
    list_filter = ('partner_also_achieved', 'achieved_at')
    search_fields = ('user__username', 'milestone__name_en')
    readonly_fields = ('achieved_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification"""
    list_display = (
        'user', 'notification_type', 'title_en', 'is_read',
        'is_sent', 'created_at'
    )
    list_filter = ('notification_type', 'is_read', 'is_sent', 'created_at')
    search_fields = ('user__username', 'title_en', 'message_en')
    readonly_fields = ('created_at', 'read_at')
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_sent', 'mark_as_read']
    
    def mark_as_sent(self, request, queryset):
        """Mark notifications as sent"""
        updated = queryset.update(is_sent=True)
        self.message_user(request, f'{updated} notifications marked as sent.')
    mark_as_sent.short_description = 'Mark selected as sent'
    
    def mark_as_read(self, request, queryset):
        """Mark notifications as read"""
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected as read'


@admin.register(SkipLimit)
class SkipLimitAdmin(admin.ModelAdmin):
    """Admin for SkipLimit"""
    list_display = ('user', 'date', 'skips_used', 'max_skips_per_day', 'can_skip_display')
    list_filter = ('date',)
    search_fields = ('user__username',)
    
    def can_skip_display(self, obj):
        """Display if user can skip"""
        return '✅' if obj.can_skip() else '❌'
    can_skip_display.short_description = 'Can Skip'


@admin.register(CoinTransaction)
class CoinTransactionAdmin(ImportExportModelAdmin):
    """Admin for CoinTransaction with import/export"""
    resource_class = CoinTransactionResource
    
    list_display = (
        'user', 'transaction_type', 'amount_display', 'balance_after',
        'description', 'created_at'
    )
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def amount_display(self, obj):
        """Display amount with color"""
        color = 'green' if obj.amount > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:+d}</span>',
            color, obj.amount
        )
    amount_display.short_description = 'Amount'


# ============================================
# ADMIN SITE CUSTOMIZATION
# ============================================

# Custom admin site title and header
admin.site.site_header = "Bonding App Administration"
admin.site.site_title = "Bonding App Admin"
admin.site.index_title = "Welcome to Bonding App Admin Panel"

# Optional: Add custom CSS for better styling
class CustomAdminSite(admin.AdminSite):
    """Custom admin site with enhanced styling"""
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['site_title'] = self.site_title
        return context
    
    
class JSONWidget(widgets.Widget):
    """Custom widget to handle JSON fields during import/export"""
    
    def clean(self, value, row=None, **kwargs):
        """Convert string to JSON (for import)"""
        if not value:
            return []
        
        # If it's already a list/dict, return it
        if isinstance(value, (list, dict)):
            return value
        
        # If it's a string, try to parse it as JSON
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # If it fails, return empty list
                return []
        
        return []
    
    def render(self, value, obj=None):
        """Convert JSON to string (for export)"""
        if value is None:
            return ""
        return json.dumps(value, ensure_ascii=False)


class ActivityResourceWithJSON(resources.ModelResource):
    """Custom Activity resource that properly handles JSON fields"""
    
    # Category as ForeignKey
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=widgets.ForeignKeyWidget(ActivityCategory, 'name_en')
    )
    
    # JSON fields with custom widget
    instructions_en = fields.Field(
        column_name='instructions_en',
        attribute='instructions_en',
        widget=JSONWidget()
    )
    instructions_hi = fields.Field(
        column_name='instructions_hi',
        attribute='instructions_hi',
        widget=JSONWidget()
    )
    materials_needed_en = fields.Field(
        column_name='materials_needed_en',
        attribute='materials_needed_en',
        widget=JSONWidget()
    )
    materials_needed_hi = fields.Field(
        column_name='materials_needed_hi',
        attribute='materials_needed_hi',
        widget=JSONWidget()
    )
    tips_en = fields.Field(
        column_name='tips_en',
        attribute='tips_en',
        widget=JSONWidget()
    )
    tips_hi = fields.Field(
        column_name='tips_hi',
        attribute='tips_hi',
        widget=JSONWidget()
    )
    questions_en = fields.Field(
        column_name='questions_en',
        attribute='questions_en',
        widget=JSONWidget()
    )
    questions_hi = fields.Field(
        column_name='questions_hi',
        attribute='questions_hi',
        widget=JSONWidget()
    )
    
    class Meta:
        model = Activity
        fields = (
            'id', 'category', 'title_en', 'title_hi', 
            'description_en', 'description_hi',
            'instructions_en', 'instructions_hi',
            'difficulty', 'estimated_time_minutes', 'best_time', 'mode',
            'materials_needed_en', 'materials_needed_hi',
            'tips_en', 'tips_hi',
            'questions_en', 'questions_hi',
            'points_reward', 'coins_reward',
            'is_premium', 'unlock_cost_coins', 
            'is_active', 'is_daily_featured'
        )
        import_id_fields = ['id']  # Use UUID as unique identifier
        skip_unchanged = True
        report_skipped = True
    
    def before_import_row(self, row, **kwargs):
        """Pre-process row before import"""
        # Ensure category exists (get or create)
        category_name = row.get('category')
        if category_name:
            category, created = ActivityCategory.objects.get_or_create(
                name_en=category_name,
                defaults={
                    'name_hi': category_name,
                    'description_en': f'{category_name} activities',
                    'description_hi': f'{category_name} गतिविधियाँ',
                    'icon': '💬',
                    'color': '#FFB6C1'
                }
            )
            row['category'] = category.name_en


# Update your ActivityAdmin to use this resource
@admin.register(Activity)
class ActivityAdmin(ImportExportModelAdmin):
    """Admin for Activity with custom JSON import/export"""
    resource_class = ActivityResourceWithJSON  # ✅ Use custom resource
    
    list_display = (
        'title_en', 'category', 'difficulty', 'estimated_time_minutes',
        'mode', 'points_reward', 'coins_reward', 'completion_count',
        'is_premium', 'is_daily_featured', 'is_active'
    )
    list_filter = (
        'category', 'difficulty', 'mode', 'best_time',
        'is_premium', 'is_daily_featured', 'is_active'
    )
    search_fields = ('title_en', 'title_hi', 'description_en', 'description_hi')
    ordering = ('-created_at',)
    list_editable = ('is_daily_featured', 'is_active')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('category', 'title_en', 'title_hi', 'description_en', 'description_hi')
        }),
        ('Instructions', {
            'fields': ('instructions_en', 'instructions_hi'),
        }),
        ('Metadata', {
            'fields': ('difficulty', 'estimated_time_minutes', 'best_time', 'mode')
        }),
        ('Materials & Tips', {
            'fields': ('materials_needed_en', 'materials_needed_hi', 'tips_en', 'tips_hi'),
        }),
        ('Questions', {
            'fields': ('questions_en', 'questions_hi'),
        }),
        ('Gamification', {
            'fields': ('points_reward', 'coins_reward', 'is_premium', 'unlock_cost_coins')
        }),
        ('Status', {
            'fields': ('is_active', 'is_daily_featured', 'completion_count', 'average_rating')
        }),
    )
    
    readonly_fields = ('completion_count', 'average_rating', 'created_at', 'updated_at')