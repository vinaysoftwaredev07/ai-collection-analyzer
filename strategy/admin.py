from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Borrower, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile so role can be edited alongside User."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    """Extended User admin with inline profile."""
    inlines = (UserProfileInline,)


@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'days_past_due', 'amount_owed',
        'hardship_indicator', 'assigned_agent', 'created_at',
    )
    list_filter = ('hardship_indicator', 'preferred_channel', 'assigned_agent')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


# Re-register User with the extended admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
