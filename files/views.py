import calendar
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.http import HttpResponse, FileResponse
from accounts.models import User

from .forms import (
    AssignmentForm,
    AssignmentSubmissionForm,
    ClassFileForm,
    FolderForm,
    NoticeBoardPostForm,
    PrivateFileForm,
)
from .models import (
    Assignment,
    AssignmentSubmission,
    ClassFile,
    FileActivity,
    Folder,
    Notification,
    NoticeBoardPost,
    PrivateFile,
    create_notification,
    log_file_activity,
)


def _get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _get_expiry_datetime(expiry_days):
    if not expiry_days:
        return None
    return timezone.now() + timezone.timedelta(days=expiry_days)


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@login_required
def create_folder_view(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.owner = request.user
            folder.save()
            messages.success(request, f'"{folder.name}" papka döredildi.')
            parent_id = request.POST.get('parent')
            if parent_id:
                return redirect(f"{request.META.get('HTTP_REFERER', 'my_files')}?folder={parent_id}")
            return redirect('my_files')
    else:
        form = FolderForm()

    return render(request, 'files/create_folder.html', {'form': form})


@login_required
def send_private_file(request, user_id):
    receiver = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = PrivateFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_size = request.FILES['file'].size
            if not request.user.has_storage_available(file_size):
                messages.error(
                    request,
                    f"Ýer çägi doldy. Sizde diňe {request.user.get_remaining_storage() / (1024 * 1024):.2f} MB boş ýer bar."
                )
                return render(request, 'files/send_file.html', {'form': form, 'receiver': receiver})

            private_file = form.save(commit=False)
            private_file.sender = request.user
            private_file.receiver = receiver
            private_file.expires_at = _get_expiry_datetime(form.cleaned_data.get('expiry_days'))
            private_file.save()

            create_notification(
                user=receiver,
                title='Täze şahsy faýl geldi',
                message=f'{request.user.username} size "{private_file.filename}" faýlyny iberdi.',
                category='file',
                level='success',
                link='/files/inbox/',
            )
            log_file_activity(
                action='upload',
                file_type='private',
                actor=request.user,
                private_file=private_file,
                description=f'{receiver.username} üçin şahsy faýl iberildi.',
                ip_address=_get_client_ip(request),
            )

            messages.success(request, f'Faýl {receiver.username} ulanyja iberildi.')
            return redirect('student_list')
    else:
        form = PrivateFileForm()

    return render(request, 'files/send_file.html', {'form': form, 'receiver': receiver})


@login_required
def class_files_view(request):
    user_class = request.user.classroom

    if not user_class:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ClassFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_size = request.FILES['file'].size

            if not request.user.has_storage_available(file_size):
                messages.error(
                    request,
                    f"Ýer çägi doldy. Sizde diňe {request.user.get_remaining_storage() / (1024 * 1024):.2f} MB boş ýer bar."
                )
                return render(request, 'files/class_files.html', {'form': form, 'files': ClassFile.objects.filter(classroom=user_class)})

            if not user_class.has_space_for(file_size):
                messages.error(
                    request,
                    f'"{user_class.name}" topary üçin bölünen ýer ýeterlik däl.'
                )
                return render(request, 'files/class_files.html', {'form': form, 'files': ClassFile.objects.filter(classroom=user_class)})

            class_file = form.save(commit=False)
            class_file.classroom = user_class
            class_file.uploaded_by = request.user
            class_file.expires_at = _get_expiry_datetime(form.cleaned_data.get('expiry_days'))
            class_file.save()

            classmates = user_class.user_set.exclude(id=request.user.id)
            for classmate in classmates:
                create_notification(
                    user=classmate,
                    title='Topara täze faýl goşuldy',
                    message=f'{request.user.username} "{class_file.filename}" faýlyny topara ýükläpdir.',
                    category='file',
                    level='info',
                    link='/files/class/',
                )

            log_file_activity(
                action='upload',
                file_type='class',
                actor=request.user,
                class_file=class_file,
                description=f'{user_class.name} toparyna täze faýl ýüklenildi.',
                ip_address=_get_client_ip(request),
            )

            messages.success(request, 'Faýl üstünlikli ýüklendi.')
            return redirect('class_files')
    else:
        form = ClassFileForm()

    files_list = ClassFile.objects.filter(classroom=user_class, is_expired=False).order_by('-created_at')
    paginator = Paginator(files_list, 10)
    page_number = request.GET.get('page')
    files = paginator.get_page(page_number)

    return render(request, 'files/class_files.html', {
        'form': form,
        'files': files,
    })


@login_required
def my_files_view(request):
    folder_id = request.GET.get('folder')

    if folder_id:
        current_folder = get_object_or_404(Folder, id=folder_id, owner=request.user)
        folders = Folder.objects.filter(owner=request.user, parent=current_folder)
        files = PrivateFile.objects.filter(sender=request.user, folder=current_folder, is_expired=False)
    else:
        current_folder = None
        folders = Folder.objects.filter(owner=request.user, parent=None)
        files = PrivateFile.objects.filter(sender=request.user, folder=None, is_expired=False)

    return render(request, 'files/my_files.html', {
        'folders': folders,
        'files': files,
        'current_folder': current_folder,
    })


@login_required
def inbox_view(request):
    files = request.user.received_files.filter(is_expired=False).order_by('-created_at')
    return render(request, 'files/inbox.html', {'files': files})


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'notifications.html', {'notifications': page_obj})


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    if notification.link:
        return redirect(notification.link)
    return redirect('notifications')


@login_required
def assignment_list_view(request):
    create_form = None
    submission_form = None
    user_class = request.user.classroom

    # Hakyky ulanyjynyň tabşyryk döredip bilmek ygtyýary barlagy (Admin ýa-da Mugallym)
    can_create = (
        request.user.is_superuser or 
        getattr(request.user, 'is_admin_role', False) or 
        getattr(request.user, 'is_teacher_role', False)
    )

    if can_create:
        assignments = Assignment.objects.select_related('classroom', 'created_by').all()
    else:
        # Talyplar diňe öz toparlaryna degişli işjeň tabşyryklary görüp biler
        assignments = Assignment.objects.select_related('classroom', 'created_by').filter(
            classroom=user_class,
            is_active=True,
        )

    # Tabşyryk döretmek POST soragy gelende (Diňe Mugallym/Admin)
    if request.method == 'POST' and request.POST.get('create_assignment'):
        if not can_create:
            messages.error(request, 'Size tabşyryk döretmäge ygtyýaryňyz ýok.')
            return redirect('assignments')
            
        create_form = AssignmentForm(request.POST, request.FILES)
        if create_form.is_valid():
            assignment = create_form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            
            # Topardaky talyplara habar ugratmak
            if assignment.classroom:
                for student in assignment.classroom.user_set.all():
                    create_notification(
                        user=student,
                        title='Täze tabşyryk döredildi',
                        message=f'"{assignment.title}" tabşyrygy size goşuldy.',
                        category='file',
                        level='info',
                        link='/files/assignments/',
                    )
            messages.success(request, 'Täze tabşyryk üstünlikli döredildi.')
            return redirect('assignments')

    # Talyplaryň ugradan jogaplaryny barlamak üçin (Diňe Talyp)
    if request.method == 'POST' and request.POST.get('submit_assignment'):
        if can_create:
            messages.error(request, 'Mugallymlar tabşyryk tabşyrip bilmeýär.')
            return redirect('assignments')

        assignment_id = request.POST.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id, is_active=True)
        
        if request.user.classroom != assignment.classroom:
            messages.error(request, 'Bu tabşyryk sizin toparyňyza degişli däl.')
            return redirect('assignments')
            
        submission_form = AssignmentSubmissionForm(request.POST, request.FILES)
        if submission_form.is_valid():
            submission, created = AssignmentSubmission.objects.update_or_create(
                assignment=assignment,
                student=request.user,
                defaults={
                    'file': submission_form.cleaned_data['file'],
                    'comment': submission_form.cleaned_data['comment'],
                }
            )
            messages.success(request, 'Tabşyryk üstünlikli tabşyryldy.')
            return redirect('assignments')
    else:
        submission_form = AssignmentSubmissionForm()

    if create_form is None and can_create:
        create_form = AssignmentForm()

    submissions_map = {}
    if request.user.is_authenticated and not can_create:
        submissions = AssignmentSubmission.objects.filter(student=request.user).select_related('assignment')
        submissions_map = {submission.assignment_id: submission for submission in submissions}

    assignment_cards = []
    for assignment in assignments:
        assignment_cards.append({
            'assignment': assignment,
            'submission': submissions_map.get(assignment.id),
            'submission_count': assignment.submissions.count(),
        })

    return render(request, 'files/assignments.html', {
        'assignment_cards': assignment_cards,
        'create_form': create_form,
        'submission_form': submission_form,
        'is_teacher_or_admin': can_create,
    })
@login_required
def deadline_calendar_view(request):
    current_date = parse_date(request.GET.get('month', '')) or timezone.localdate().replace(day=1)
    month_start = current_date.replace(day=1)
    cal = calendar.Calendar(firstweekday=0)

    assignments = Assignment.objects.filter(
        is_active=True,
        due_date__year=month_start.year,
        due_date__month=month_start.month,
    )
    if not request.user.is_teacher_role:
        assignments = assignments.filter(classroom=request.user.classroom)

    expiring_private = PrivateFile.objects.filter(
        is_expired=False,
        expires_at__year=month_start.year,
        expires_at__month=month_start.month,
    )
    if not request.user.is_admin_role:
        expiring_private = expiring_private.filter(receiver=request.user)

    expiring_class = ClassFile.objects.filter(
        is_expired=False,
        expires_at__year=month_start.year,
        expires_at__month=month_start.month,
    )
    if not request.user.is_teacher_role:
        expiring_class = expiring_class.filter(classroom=request.user.classroom)

    events_by_day = defaultdict(list)
    for assignment in assignments:
        events_by_day[assignment.due_date.date()].append({
            'type': 'assignment',
            'title': assignment.title,
            'meta': assignment.classroom.name,
        })
    for file_obj in expiring_private:
        if file_obj.expires_at:
            events_by_day[file_obj.expires_at.date()].append({
                'type': 'private_file',
                'title': file_obj.filename,
                'meta': 'Şahsy faýl',
            })
    for file_obj in expiring_class:
        if file_obj.expires_at:
            events_by_day[file_obj.expires_at.date()].append({
                'type': 'class_file',
                'title': file_obj.filename,
                'meta': file_obj.classroom.name,
            })

    weeks = []
    for week in cal.monthdatescalendar(month_start.year, month_start.month):
        week_days = []
        for day in week:
            week_days.append({
                'date': day,
                'is_current_month': day.month == month_start.month,
                'is_today': day == timezone.localdate(),
                'events': events_by_day.get(day, []),
            })
        weeks.append(week_days)

    prev_month = (month_start - timezone.timedelta(days=1)).replace(day=1)
    next_month = (month_start + timezone.timedelta(days=32)).replace(day=1)

    return render(request, 'files/deadline_calendar.html', {
        'weeks': weeks,
        'month_start': month_start,
        'prev_month': prev_month,
        'next_month': next_month,
        'weekday_names': ['Du', 'Si', 'Ça', 'Pe', 'An', 'Şe', 'Ýe'],
    })


def notice_board_view(request):
    posts = NoticeBoardPost.objects.filter(is_published=True).select_related('author')

    if request.method == 'POST':
        if not request.user.is_authenticated or not request.user.is_teacher_role:
            return redirect('notice_board')
        form = NoticeBoardPostForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.author = request.user
            notice.save()
            for user in User.objects.filter(is_active=True):
                create_notification(
                    user=user,
                    title='Täze umumy bildiriş',
                    message=f'"{notice.title}" umumy tagta goşuldy.',
                    category='system',
                    level='info',
                    link='/files/notice-board/',
                )
            messages.success(request, 'Bildiriş tagta goşuldy.')
            return redirect('notice_board')
    else:
        form = NoticeBoardPostForm() if request.user.is_authenticated and request.user.is_teacher_role else None

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'files/notice_board.html', {
        'posts': page_obj,
        'form': form,
        'can_post': request.user.is_authenticated and request.user.is_teacher_role,
    })


@login_required
def download_private_file(request, file_id):
    private_file = get_object_or_404(PrivateFile, id=file_id, is_expired=False)

    if request.user != private_file.sender and request.user != private_file.receiver and not request.user.is_admin_role:
        return redirect('dashboard')

    log_file_activity(
        action='download',
        file_type='private',
        actor=request.user,
        private_file=private_file,
        description='Şahsy faýl göçürildi.',
        ip_address=_get_client_ip(request),
    )
    return FileResponse(
        private_file.file.open('rb'),
        as_attachment=True,
        filename=private_file.filename,
    )


@login_required
def download_class_file(request, file_id):
    class_file = get_object_or_404(ClassFile, id=file_id, is_expired=False)

    if request.user.classroom != class_file.classroom and not request.user.is_admin_role:
        return redirect('dashboard')

    log_file_activity(
        action='download',
        file_type='class',
        actor=request.user,
        class_file=class_file,
        description='Topar faýly göçürildi.',
        ip_address=_get_client_ip(request),
    )
    return FileResponse(
        class_file.file.open('rb'),
        as_attachment=True,
        filename=class_file.filename,
    )


@login_required
def preview_private_file(request, file_id):
    private_file = get_object_or_404(PrivateFile, id=file_id, is_expired=False)

    if request.user != private_file.sender and request.user != private_file.receiver and not request.user.is_admin_role:
        return redirect('dashboard')

    log_file_activity(
        action='preview',
        file_type='private',
        actor=request.user,
        private_file=private_file,
        description='Şahsy faýl görüldi.',
        ip_address=_get_client_ip(request),
    )
    return render(request, 'files/file_preview.html', {
        'file_obj': private_file,
        'file_type': 'private',
    })

@login_required
def preview_private_file_content(request, file_id):
    file_obj = get_object_or_404(PrivateFile, id=file_id)
    
    # Eger faýl tekst (.txt we ş.m.) bolsa, ony dogry utf-8 bilen okaýarys
    if file_obj.preview_kind == 'text':
        file_path = file_obj.file.path
        try:
            # Ilki UTF-8 barläris, başa barmasa cp1252 (Windows) arkaly okaýarys
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='cp1252', errors='ignore') as f:
                content = f.read()
                
        from django.http import HttpResponse
        return HttpResponse(content, content_type='text/plain; charset=utf-8')
    
    # Beýleki faýllar adaty ýagdaýda açylýar...

@login_required
def preview_class_file(request, file_id):
    class_file = get_object_or_404(ClassFile, id=file_id, is_expired=False)

    if request.user.classroom != class_file.classroom and not request.user.is_admin_role:
        return redirect('dashboard')

    log_file_activity(
        action='preview',
        file_type='class',
        actor=request.user,
        class_file=class_file,
        description='Topar faýly görüldi.',
        ip_address=_get_client_ip(request),
    )
    return render(request, 'files/file_preview.html', {
        'file_obj': class_file,
        'file_type': 'class',
    })


@login_required
def preview_class_file_content(request, file_id):
    class_file = get_object_or_404(ClassFile, id=file_id, is_expired=False)

    if request.user.classroom != class_file.classroom and not request.user.is_admin_role:
        return redirect('dashboard')

    return FileResponse(
        class_file.file.open('rb'),
        as_attachment=False,
        filename=class_file.filename,
        content_type=class_file.mime_type,
    )


@user_passes_test(_is_admin)
def admin_file_history(request):
    activities = FileActivity.objects.select_related('actor', 'private_file', 'class_file').all()

    action = request.GET.get('action')
    file_type = request.GET.get('file_type')
    username = request.GET.get('user')

    if action:
        activities = activities.filter(action=action)
    if file_type:
        activities = activities.filter(file_type=file_type)
    if username:
        activities = activities.filter(actor__username__icontains=username)

    paginator = Paginator(activities, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_file_history.html', {
        'activities': page_obj,
        'selected_action': action or '',
        'selected_file_type': file_type or '',
        'search_user': username or '',
        'action_choices': FileActivity.ACTION_CHOICES,
        'file_type_choices': FileActivity.FILE_TYPE_CHOICES,
    })

@login_required
def preview_private_file_content(request, file_id):
    file_obj = get_object_or_404(PrivateFile, id=file_id)
    
    # Eger tekst faýl bolsa, content üýtgeýän aňlatmasyna okap berýäris
    text_content = ""
    if file_obj.preview_kind == 'text':
        try:
            with open(file_obj.file.path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
        except UnicodeDecodeError:
            with open(file_obj.file.path, 'r', encoding='cp1252', errors='ignore') as f:
                text_content = f.read()
        return HttpResponse(text_content, content_type='text/plain; charset=utf-8')

    from django.http import FileResponse
    return FileResponse(file_obj.file.open('rb'))
@login_required
def delete_private_file(request, file_id):
    file_obj = get_object_or_404(PrivateFile, id=file_id)
    
    # Diňe kabul ediji ýa-da ugradyjy bu faýly pozup biler
    if request.user == file_obj.receiver or request.user == file_obj.sender:
        file_obj.delete()
        messages.success(request, 'Faýl üstünlikli pozuldy.')
    else:
        messages.error(request, 'Bu faýly pozmaga ygtyýaryňyz ýok.')
        
    return redirect('inbox') # ýa-da gelen hatlar sahypanyň ady näme bolsa şol


from django.http import HttpResponse, FileResponse

@login_required
def preview_assignment_attachment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Topar barlagy
    can_create = request.user.is_superuser or getattr(request.user, 'is_admin_role', False) or getattr(request.user, 'is_teacher_role', False)
    if not can_create and request.user.classroom != assignment.classroom:
        return redirect('assignments')

    if assignment.attachment:
        file_path = assignment.attachment.path
        if assignment.attachment.name.lower().endswith('.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='cp1252', errors='ignore') as f:
                    content = f.read()
            return HttpResponse(content, content_type='text/plain; charset=utf-8')

    return FileResponse(assignment.attachment.open('rb'))


@login_required
def preview_assignment_file_content(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    
    can_create = request.user.is_superuser or getattr(request.user, 'is_admin_role', False) or getattr(request.user, 'is_teacher_role', False)
    if request.user != submission.student and not can_create:
        return redirect('assignments')

    if submission.file:
        file_path = submission.file.path
        if submission.file.name.lower().endswith('.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='cp1252', errors='ignore') as f:
                    content = f.read()
            return HttpResponse(content, content_type='text/plain; charset=utf-8')

    return FileResponse(submission.file.open('rb'))