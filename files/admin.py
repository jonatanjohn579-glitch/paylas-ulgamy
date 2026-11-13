from django.contrib import admin

from .models import (
    Assignment,
    AssignmentSubmission,
    ClassFile,
    FileActivity,
    Folder,
    NoticeBoardPost,
    Notification,
    PrivateFile,
)


@admin.register(PrivateFile)
class PrivateFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'sender', 'receiver', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('is_expired', 'created_at')
    search_fields = ('file', 'sender__username', 'receiver__username')


@admin.register(ClassFile)
class ClassFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'classroom', 'uploaded_by', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('classroom', 'is_expired', 'created_at')
    search_fields = ('file', 'uploaded_by__username', 'classroom__name')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'level', 'is_read', 'created_at')
    list_filter = ('category', 'level', 'is_read', 'is_system')
    search_fields = ('title', 'message', 'user__username')


@admin.register(FileActivity)
class FileActivityAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'file_type', 'action', 'file_name')
    list_filter = ('file_type', 'action', 'created_at')
    search_fields = ('actor__username', 'description')


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'parent', 'created_at')
    search_fields = ('name', 'owner__username')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'created_by', 'due_date', 'is_active')
    list_filter = ('classroom', 'is_active', 'due_date')
    search_fields = ('title', 'description', 'created_by__username')


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at')
    list_filter = ('submitted_at', 'assignment__classroom')
    search_fields = ('assignment__title', 'student__username')


@admin.register(NoticeBoardPost)
class NoticeBoardPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_pinned', 'is_published', 'created_at')
    list_filter = ('is_pinned', 'is_published', 'created_at')
    search_fields = ('title', 'content', 'author__username')
