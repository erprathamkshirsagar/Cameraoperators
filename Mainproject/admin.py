from django.contrib import admin
from .models import UserRegistration, UserVerification, Skill

# -----------------------------
# User Registration Admin
# -----------------------------
@admin.register(UserRegistration)
class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'surname', 'email', 'is_freelancer', 'profile_status')
    search_fields = ('first_name', 'surname', 'email', 'mobile')
    list_filter = ('profile_status', 'is_freelancer', 'country', 'state', 'city')
    ordering = ('first_name',)

# -----------------------------
# User Verification Admin
# -----------------------------
@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'status')
    search_fields = ('user__first_name', 'user__surname', 'user__email', 'document__name')
    list_filter = ('status',)
    ordering = ('user',)

# -----------------------------
# Skill Admin
# -----------------------------
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'rate', 'created_at')
    search_fields = ('user__first_name', 'user__surname', 'user__email', 'category__name')
    list_filter = ('category',)
    ordering = ('-created_at',)
