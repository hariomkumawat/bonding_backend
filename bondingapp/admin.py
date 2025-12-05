from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django import forms
from .models import (
    User, UserPreference, ActivityCategory, Activity, ActivitySession,
    ActivityCompletion, Streak, Badge, UserBadge, Milestone, UserMilestone,
    Notification, SkipLimit, CoinTransaction
)


# Corrected UserCreationForm - Remove the invalid BaseUserAdmin reference
class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'username')  # Include username if required; adjust as needed
        field_classes = {'username': forms.CharField}  # Optional: Customize fields


# UserChangeForm is already mostly correct, but ensure Meta is standalone
class UserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'  # Or specify: ('email', 'username', ...) for security


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active',
        'age', 'current_level', 'total_points', 'coins', 'is_online', 'last_active'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'is_online', 'preferred_language', 'theme',
        'current_level', 'age', ('created_at', admin.DateFieldListFilter),
        ('last_active', admin.DateFieldListFilter)
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'google_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('email', 'first_name', 'last_name', 'age', 'profile_picture', 'bio')
        }),
        (_('Authentication'), {
            'fields': ('google_id', 'phone_number', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Relationship'), {
            'fields': ('partner', 'relationship_start_date', 'partner_invitation_code')
        }),
        (_('Preferences'), {
            'fields': ('preferred_language', 'theme')
        }),
        (_('Gamification'), {
            'fields': ('total_points', 'current_level', 'coins')
        }),
        (_('Status'), {
            'fields': ('is_online', 'last_active')
        }),
        (_('Important dates'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    ordering = ('-created_at',)
    filter_horizontal = ('groups', 'user_permissions',)

    def generate_invitation_code(self, request, obj):
        if not obj.partner_invitation_code:
            obj.generate_invitation_code()
            self.message_user(request, f'Invitation code generated: {obj.partner_invitation_code}')
        else:
            self.message_user(request, f'Invitation code already exists: {obj.partner_invitation_code}', level='warning')

    generate_invitation_code.short_description = 'Generate Partner Invitation Code'
    actions = [generate_invitation_code]
class UserPreferenceInline(admin.StackedInline):
    model = UserPreference
    fields = (
        'daily_reminder_enabled', 'daily_reminder_time', 'partner_activity_alerts',
        'streak_reminders', 'milestone_notifications', 'sound_enabled', 'vibration_enabled',
        'activity_difficulty', 'notification_frequency'
    )
    extra = 0
    can_delete = False


class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    fields = ('badge', 'unlocked_at', 'is_displayed')
    readonly_fields = ('unlocked_at',)
    extra = 0


class UserMilestoneInline(admin.TabularInline):
    model = UserMilestone
    fields = ('milestone', 'achieved_at', 'partner_also_achieved')
    readonly_fields = ('achieved_at',)
    extra = 0


class ActivityCompletionInline(admin.TabularInline):
    model = ActivityCompletion
    fields = ('activity', 'rating', 'points_earned', 'coins_earned', 'shared_with_partner', 'completed_at')
    readonly_fields = ('completed_at',)
    extra = 0


class StreakInline(admin.StackedInline):
    model = Streak
    fields = ('current_streak', 'longest_streak', 'last_activity_date', 'total_active_days', 'streak_start_date')
    extra = 0
    can_delete = False


# Extend UserAdmin with inlines if needed, but since User is already registered, we can add inlines via get_inline_instances
class UserAdminWithInlines(UserAdmin):
    inlines = [UserPreferenceInline, UserBadgeInline, UserMilestoneInline, ActivityCompletionInline, StreakInline]

# Note: To use inlines, uncomment below and comment out the plain UserAdmin register
# admin.site.unregister(User)
# admin.site.register(User, UserAdminWithInlines)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_reminder_enabled', 'activity_difficulty', 'notification_frequency', 'updated_at')
    list_filter = ('daily_reminder_enabled', 'partner_activity_alerts', 'streak_reminders', 'activity_difficulty', 'notification_frequency')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Notifications', {
            'fields': ('daily_reminder_enabled', 'daily_reminder_time', 'partner_activity_alerts', 'streak_reminders', 'milestone_notifications')
        }),
        ('Sound & Vibration', {'fields': ('sound_enabled', 'vibration_enabled')}),
        ('Activity Preferences', {'fields': ('activity_difficulty', 'notification_frequency')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ('-updated_at',)


@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'icon', 'color', 'display_order', 'is_active', 'created_at')
    list_filter = ('is_active', 'display_order')
    search_fields = ('name_en', 'name_hi', 'description_en', 'description_hi')
    list_editable = ('display_order', 'is_active')
    fieldsets = (
        ('Basic Info', {'fields': ('name_en', 'name_hi', 'icon', 'color', 'display_order', 'is_active')}),
        ('Descriptions', {'fields': ('description_en', 'description_hi')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('display_order', 'name_en')


# class ActivityInline(admin.TabularInline):
#     model = Activity
#     fields = ('title_en', 'difficulty', 'mode', 'is_active', 'is_daily_featured')
#     extra = 0
#     show_change_link = True


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title_en', 'category', 'difficulty', 'mode', 'estimated_time_minutes', 'points_reward', 'coins_reward', 'is_premium', 'is_active', 'completion_count', 'is_daily_featured')  # Added 'is_daily_featured'
    list_filter = (
        'category', 'difficulty', 'best_time', 'mode', 'is_premium', 'is_active', 'is_daily_featured',
        ('created_at', admin.DateFieldListFilter)
    )
    search_fields = ('title_en', 'title_hi', 'description_en', 'description_hi')
    list_editable = ('is_active', 'is_daily_featured')
    # inlines = [ActivityInline]  # Self-referential if needed, but typically not
    fieldsets = (
        ('Category & Metadata', {'fields': ('category', 'difficulty', 'estimated_time_minutes', 'best_time', 'mode')}),
        ('Content (English)', {
            'fields': ('title_en', 'description_en', 'instructions_en', 'materials_needed_en', 'tips_en', 'questions_en')
        }),
        ('Content (Hindi)', {
            'fields': ('title_hi', 'description_hi', 'instructions_hi', 'materials_needed_hi', 'tips_hi', 'questions_hi')
        }),
        ('Gamification & Premium', {
            'fields': ('points_reward', 'coins_reward', 'is_premium', 'unlock_cost_coins')
        }),
        ('Status & Analytics', {'fields': ('is_active', 'is_daily_featured', 'completion_count', 'average_rating')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at', 'completion_count', 'average_rating')
    ordering = ('-is_daily_featured', 'title_en')


@admin.register(ActivitySession)
class ActivitySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'status', 'mode', 'started_at', 'completed_at', 'time_spent_seconds')
    list_filter = ('status', 'mode', ('started_at', admin.DateFieldListFilter), ('completed_at', admin.DateFieldListFilter))
    search_fields = ('user__username', 'activity__title_en')
    readonly_fields = ('id', 'started_at', 'completed_at')
    fieldsets = (
        ('User & Activity', {'fields': ('user', 'activity', 'status', 'mode')}),
        ('Partner', {'fields': ('partner_session',)}),
        ('Timing', {'fields': ('started_at', 'completed_at', 'time_spent_seconds')}),
    )
    ordering = ('-started_at',)


# class ActivityCompletionInlineAdmin(ActivityCompletionInline):
#     max_num = 10


@admin.register(ActivityCompletion)
class ActivityCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'session', 'rating', 'points_earned', 'coins_earned', 'shared_with_partner', 'completed_at')
    list_filter = ('shared_with_partner', 'rating', ('completed_at', admin.DateFieldListFilter))
    search_fields = ('user__username', 'activity__title_en')
    readonly_fields = ('id', 'session', 'completed_at', 'points_earned', 'coins_earned')
    # inlines = [ActivityCompletionInlineAdmin]  # Not typically needed, but for responses if extended
    fieldsets = (
        ('User & Activity', {'fields': ('user', 'activity', 'session')}),
        ('Responses', {'fields': ('responses', 'photos', 'notes')}),
        ('Feedback', {'fields': ('rating', 'feedback')}),
        ('Rewards', {'fields': ('points_earned', 'coins_earned', 'shared_with_partner')}),
        ('Timing', {'fields': ('completed_at',)}),
    )
    ordering = ('-completed_at',)


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_activity_date', 'total_active_days')
    list_filter = ('current_streak', ('last_activity_date', admin.DateFieldListFilter))
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Streak Data', {
            'fields': ('current_streak', 'longest_streak', 'last_activity_date', 'total_active_days', 'streak_start_date')
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ('-current_streak', '-last_activity_date',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'icon', 'category', 'rarity', 'display_order', 'is_active', 'criteria')
    list_filter = ('category', 'rarity', 'is_active', 'display_order')
    search_fields = ('name_en', 'name_hi', 'description_en', 'description_hi')
    list_editable = ('display_order', 'is_active')
    fieldsets = (
        ('Basic Info', {'fields': ('name_en', 'name_hi', 'icon', 'category', 'rarity', 'display_order', 'is_active')}),
        ('Descriptions', {'fields': ('description_en', 'description_hi')}),
        ('Criteria & Rewards', {'fields': ('criteria', 'points_reward', 'coins_reward')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at',)


# class UserBadgeInlineAdmin(UserBadgeInline):
#     max_num = 20


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'unlocked_at', 'is_displayed')
    list_filter = ('is_displayed', 'badge__category', 'badge__rarity', ('unlocked_at', admin.DateFieldListFilter))
    search_fields = ('user__username', 'badge__name_en')
    readonly_fields = ('id', 'unlocked_at')
    # inlines = [UserBadgeInlineAdmin]
    fieldsets = (
        ('User & Badge', {'fields': ('user', 'badge', 'is_displayed')}),
        ('Timing', {'fields': ('unlocked_at',)}),
    )
    ordering = ('-unlocked_at',)


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'icon', 'milestone_type', 'criteria_value', 'points_reward', 'coins_reward', 'is_active')
    list_filter = ('milestone_type', 'is_active')
    search_fields = ('name_en', 'name_hi', 'description_en', 'description_hi')
    fieldsets = (
        ('Basic Info', {'fields': ('name_en', 'name_hi', 'icon', 'milestone_type', 'is_active')}),
        ('Descriptions', {'fields': ('description_en', 'description_hi')}),
        ('Criteria & Rewards', {'fields': ('criteria_value', 'points_reward', 'coins_reward')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at',)


# class UserMilestoneInlineAdmin(UserMilestoneInline):
#     max_num = 15


@admin.register(UserMilestone)
class UserMilestoneAdmin(admin.ModelAdmin):
    list_display = ('user', 'milestone', 'achieved_at', 'partner_also_achieved')
    list_filter = ('partner_also_achieved', 'milestone__milestone_type', ('achieved_at', admin.DateFieldListFilter))
    search_fields = ('user__username', 'milestone__name_en')
    readonly_fields = ('id', 'achieved_at')
    # inlines = [UserMilestoneInlineAdmin]
    fieldsets = (
        ('User & Milestone', {'fields': ('user', 'milestone', 'partner_also_achieved')}),
        ('Timing', {'fields': ('achieved_at',)}),
    )
    ordering = ('-achieved_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title_en', 'is_read', 'is_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent', ('created_at', admin.DateFieldListFilter))
    search_fields = ('user__username', 'title_en', 'title_hi', 'message_en', 'message_hi')
    readonly_fields = ('id', 'created_at', 'read_at')
    list_editable = ('is_read', 'is_sent')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Content', {'fields': ('notification_type', 'title_en', 'title_hi', 'message_en', 'message_hi', 'data')}),
        ('Status', {'fields': ('is_read', 'is_sent', 'read_at')}),
        ('Timing', {'fields': ('created_at',)}),
    )
    ordering = ('-created_at',)
    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'


@admin.register(SkipLimit)
class SkipLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'skips_used', 'max_skips_per_day', 'can_skip')
    list_filter = (('date', admin.DateFieldListFilter),)
    search_fields = ('user__username',)
    readonly_fields = ('date',)

    def can_skip(self, obj):
        return obj.can_skip()
    can_skip.boolean = True
    can_skip.short_description = 'Can Skip More?'

    fieldsets = (
        ('User & Date', {'fields': ('user', 'date')}),
        ('Limits', {'fields': ('skips_used', 'max_skips_per_day')}),
    )
    ordering = ('-date', 'user')


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'balance_after', 'description', 'created_at')
    list_filter = ('transaction_type', ('created_at', admin.DateFieldListFilter))
    search_fields = ('user__username', 'description', 'related_object_id')
    readonly_fields = ('id', 'created_at', 'balance_after')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Transaction', {
            'fields': ('transaction_type', 'amount', 'balance_after', 'description', 'related_object_id', 'related_object_type')
        }),
        ('Timing', {'fields': ('created_at',)}),
    )
    ordering = ('-created_at',)