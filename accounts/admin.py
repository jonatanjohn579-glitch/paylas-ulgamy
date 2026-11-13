from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClassRoom


class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_storage_used_display', 'storage_quota_display')
    readonly_fields = ('get_storage_used_display',)

    def get_storage_used_display(self, obj):
        used = obj.get_storage_used() or 0
        return self._format_bytes(used)

    get_storage_used_display.short_description = 'Used'

    def storage_quota_display(self, obj):
        quota = obj.storage_quota or 0
        return self._format_bytes(quota)

    storage_quota_display.short_description = 'Quota'

    def _format_bytes(self, bytes_val):
        try:
            b = float(bytes_val)
        except Exception:
            return '0 B'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024:
                return f"{b:.2f} {unit}"
            b /= 1024
        return f"{b:.2f} TB"


admin.site.register(ClassRoom, ClassRoomAdmin)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = UserAdmin.list_display + ('role', 'classroom')
    list_filter = UserAdmin.list_filter + ('role', 'classroom')
    
    # Ulanyjynyň içine girip üýtgetmek ýa-da döretmek isleýän wagtyňyz görünjek meýdançalar
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Class Settings', {
            'fields': ('role', 'classroom'),
        }),
        ('Storage Settings', {
            'fields': ('storage_quota', 'get_storage_used_display', 'get_remaining_storage_display'),
            'classes': ('collapse',),
        }),
        ('Additional Info', {
            'fields': ('profile_image',),
        }),
    )
    
    # Täze ulanyjy goşulýan wagtda (add user) aşakda görünjek meýdançalar
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Class Settings', {
            'fields': ('role', 'classroom'),
        }),
    )
    
    readonly_fields = ('get_storage_used_display', 'get_remaining_storage_display')
    
    def get_storage_used_display(self, obj):
        used = obj.get_total_storage_used()
        quota = obj.storage_quota
        percentage = obj.get_storage_percentage()
        
        def format_bytes(bytes_val):
            try:
                b = float(bytes_val)
            except Exception:
                return '0 B'
            for unit in ['B', 'KB', 'MB', 'GB']:
                if b < 1024:
                    return f"{b:.2f} {unit}"
                b /= 1024
            return f"{b:.2f} TB"
        
        return f"{format_bytes(used)} / {format_bytes(quota)} ({percentage}%)"
    
    get_storage_used_display.short_description = "Storage Used"
    
    def get_remaining_storage_display(self, obj):
        remaining = obj.get_remaining_storage()
        
        def format_bytes(bytes_val):
            try:
                b = float(bytes_val)
            except Exception:
                return '0 B'
            for unit in ['B', 'KB', 'MB', 'GB']:
                if b < 1024:
                    return f"{b:.2f} {unit}"
                b /= 1024
            return f"{b:.2f} TB"
        
        return format_bytes(remaining)
    
    get_remaining_storage_display.short_description = "Remaining Storage"