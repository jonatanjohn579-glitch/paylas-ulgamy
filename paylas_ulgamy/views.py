from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils.timezone import now

from accounts.models import ClassRoom, User
from files.models import ClassFile, FileActivity, Notification, PrivateFile, run_file_lifecycle_checks


def home(request):
    return redirect('dashboard')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


def is_admin(user):
    return user.is_authenticated and user.is_admin_role


def format_size(size_bytes):
    if size_bytes < 1024:
        return f'{size_bytes} B'
    if size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.2f} KB'
    if size_bytes < 1024 * 1024 * 1024:
        return f'{size_bytes / (1024 * 1024):.2f} MB'
    return f'{size_bytes / (1024 * 1024 * 1024):.2f} GB'


@user_passes_test(is_admin)
def admin_dashboard(request):
    from .system_health import format_bytes, get_system_health

    lifecycle_stats = run_file_lifecycle_checks()

    if request.method == 'POST' and request.POST.get('update_class_quotas'):
        classes = ClassRoom.objects.all()
        updated = []
        for classroom in classes:
            key = f'quota_{classroom.id}'
            value = request.POST.get(key)
            if value is None:
                continue
            try:
                mb = float(value)
                bytes_value = int(mb * 1024 * 1024)
                if classroom.storage_quota != bytes_value:
                    classroom.storage_quota = bytes_value
                    classroom.save()
                    updated.append(classroom.name)
            except ValueError:
                continue
        if updated:
            messages.success(request, f"Kwotalar täzelendi: {', '.join(updated)}")
        else:
            messages.info(request, 'Hiç hili kwota üýtgemedi.')
        return redirect('admin_dashboard')

    class_student_counts = ClassRoom.objects.annotate(student_count=Count('user'))
    class_file_counts = ClassRoom.objects.annotate(file_count=Count('classfile'))

    today = now().date()
    today_private = PrivateFile.objects.filter(created_at__date=today).count()
    today_class = ClassFile.objects.filter(created_at__date=today).count()
    today_private_files = PrivateFile.objects.filter(created_at__date=today).order_by('-created_at')[:10]
    today_class_files = ClassFile.objects.filter(created_at__date=today).order_by('-created_at')[:10]

    total_users = User.objects.count()
    total_private = PrivateFile.objects.count()
    total_class = ClassFile.objects.count()

    total_size_bytes = 0
    for file_obj in PrivateFile.objects.filter(is_expired=False):
        if file_obj.file and hasattr(file_obj.file, 'size') and file_obj.file.size:
            total_size_bytes += file_obj.file.size
    for file_obj in ClassFile.objects.filter(is_expired=False):
        if file_obj.file and hasattr(file_obj.file, 'size') and file_obj.file.size:
            total_size_bytes += file_obj.file.size

    total_size_formatted = format_size(total_size_bytes)

    user_file_sizes = []
    users = User.objects.exclude(is_superuser=True).exclude(role=User.ROLE_ADMIN)
    for user in users:
        user_size = 0
        for file_obj in user.sent_files.filter(is_expired=False):
            if file_obj.file and hasattr(file_obj.file, 'size') and file_obj.file.size:
                user_size += file_obj.file.size
        for file_obj in user.received_files.filter(is_expired=False):
            if file_obj.file and hasattr(file_obj.file, 'size') and file_obj.file.size:
                user_size += file_obj.file.size
        for file_obj in user.classfile_set.filter(is_expired=False):
            if file_obj.file and hasattr(file_obj.file, 'size') and file_obj.file.size:
                user_size += file_obj.file.size
        if user_size > 0:
            user_file_sizes.append({
                'user': user,
                'size_bytes': user_size,
                'size_formatted': format_size(user_size),
                'storage_percent': user.get_storage_percentage(),
                'storage_remaining': format_bytes(user.get_remaining_storage()),
            })
    user_file_sizes.sort(key=lambda item: item['size_bytes'], reverse=True)
    top_users = user_file_sizes[:5]

    recent_activities = FileActivity.objects.select_related('actor', 'private_file', 'class_file')[:15]
    recent_system_notifications = Notification.objects.filter(is_system=True)[:10]

    stats_cards = {
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
        'system_alerts': Notification.objects.filter(is_system=True, is_read=False).count(),
        'downloads_today': FileActivity.objects.filter(action='download', created_at__date=today).count(),
        'previews_today': FileActivity.objects.filter(action='preview', created_at__date=today).count(),
        'expiring_soon': lifecycle_stats['expiring_soon'],
        'auto_deleted': lifecycle_stats['deleted'],
    }

    classes = ClassRoom.objects.all()
    classes_data = []
    for classroom in classes:
        used = classroom.get_storage_used() or 0
        quota_mb = (classroom.storage_quota or 0) / (1024 * 1024)
        classes_data.append({
            'id': classroom.id,
            'name': classroom.name,
            'quota_mb': f'{quota_mb:.2f}',
            'quota_bytes': classroom.storage_quota or 0,
            'used_bytes': used,
            'used_formatted': format_bytes(used),
        })

    context = {
        'class_student_counts': class_student_counts,
        'class_file_counts': class_file_counts,
        'today_private': today_private,
        'today_class': today_class,
        'total_users': total_users,
        'total_private': total_private,
        'total_class': total_class,
        'today_private_files': today_private_files,
        'today_class_files': today_class_files,
        'total_size_bytes': total_size_bytes,
        'total_size_formatted': total_size_formatted,
        'today': today,
        'top_users': top_users,
        'system_health': get_system_health(),
        'classes': classes_data,
        'recent_activities': recent_activities,
        'recent_system_notifications': recent_system_notifications,
        'stats_cards': stats_cards,
    }
    return render(request, 'admin_dashboard.html', context)
