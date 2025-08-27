from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserAuditLog, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('is_active', 'is_verified', 'date_joined')
    search_fields = ('email', 'username')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'deactivated_at')}),
        ('OIDC Info', {'fields': ('oidc_subject', 'oidc_issuer')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'action', 'details')
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'show_profile', 'location', 'created_at')
    list_filter = ('show_profile', 'created_at')
    search_fields = ('user__email', 'user__username', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'bio', 'location')
        }),
        ('Media', {
            'fields': ('avatar',)
        }),
        ('Privacy Settings', {
            'fields': ('show_email', 'show_profile', 'data_processing_consent', 'marketing_consent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
