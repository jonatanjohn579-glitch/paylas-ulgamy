from django.urls import path
from .views import (
    admin_file_history,
    assignment_list_view,
    class_files_view,
    create_folder_view,
    deadline_calendar_view,
    download_class_file,
    download_private_file,
    inbox_view,
    mark_notification_read,
    my_files_view,
    notifications_view,
    notice_board_view,
    preview_class_file,
    preview_class_file_content,
    preview_private_file,
    preview_private_file_content,
    send_private_file,
    delete_private_file,
    preview_assignment_attachment,        # <--- Import edilmeli
    preview_assignment_file_content,      # <--- Import edilmeli
)

urlpatterns = [
    path('send/<int:user_id>/', send_private_file, name='send_private_file'),
    path('class/', class_files_view, name='class_files'),
    path('assignments/', assignment_list_view, name='assignments'),
    path('calendar/', deadline_calendar_view, name='deadline_calendar'),
    path('inbox/', inbox_view, name='inbox'),
    path('notice-board/', notice_board_view, name='notice_board'),
    path('download/<int:file_id>/', download_private_file, name='download_private_file'),
    path('class-download/<int:file_id>/', download_class_file, name='download_class_file'),
    path('preview/private/<int:file_id>/', preview_private_file, name='preview_private_file'),
    path('preview/private/<int:file_id>/content/', preview_private_file_content, name='preview_private_file_content'),
    path('preview/class/<int:file_id>/', preview_class_file, name='preview_class_file'),
    path('preview/class/<int:file_id>/content/', preview_class_file_content, name='preview_class_file_content'),
    path('my-files/', my_files_view, name='my_files'),
    path('create-folder/', create_folder_view, name='create_folder'),
    path('notifications/', notifications_view, name='notifications'),
    path('file/delete/<int:file_id>/', delete_private_file, name='delete_private_file'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('admin-history/', admin_file_history, name='admin_file_history'),
    
    # ─── MÖHÜM: Şu iki url hökmany bolmaly ───
    path('assignments/preview-attachment/<int:assignment_id>/', preview_assignment_attachment, name='preview_assignment_attachment'),
    path('assignments/preview/<int:submission_id>/', preview_assignment_file_content, name='preview_assignment_file'),
]