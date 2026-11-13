import mimetypes
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import ClassRoom

User = settings.AUTH_USER_MODEL

def validate_file_size(value):
    limit = 10 * 1024 * 1024  # 10MB
    if value.size > limit:
        raise ValidationError("Faýlyň göwrümi juda uly. Iň uly rugsat berilýän möhlet: 10MB.")

def validate_file_type(value):
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = [
        '.pdf', '.jpg', '.jpeg', '.png', '.gif',
        '.doc', '.docx', '.txt', '.xls', '.xlsx',
        '.ppt', '.pptx', '.mp4', '.mp3'
    ]
    if ext not in allowed_extensions:
        raise ValidationError(f"Bu faýl görnüşi rugsat edilmeýär. Rugsat edilenler: {', '.join(allowed_extensions)}")

class Folder(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='folders'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'owner', 'parent']
        verbose_name = "Papka"
        verbose_name_plural = "Papkalar"
    
    def __str__(self):
        return self.name


class FilePreviewMixin(models.Model):
    class Meta:
        abstract = True

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else ''

    @property
    def extension(self):
        return os.path.splitext(self.filename)[1].lower()

    @property
    def mime_type(self):
        mime_type, _ = mimetypes.guess_type(self.filename)
        return mime_type or 'application/octet-stream'

    @property
    def preview_kind(self):
        mime_type = self.mime_type
        if mime_type.startswith('image/'):
            return 'image'
        if mime_type == 'application/pdf':
            return 'pdf'
        if mime_type.startswith('text/'):
            return 'text'
        if mime_type.startswith('audio/'):
            return 'audio'
        if mime_type.startswith('video/'):
            return 'video'
        if self.extension in {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}:
            return 'document'
        return 'binary'

    @property
    def can_preview(self):
        return self.preview_kind in {'image', 'pdf', 'text', 'audio', 'video', 'document'}

    def is_file_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def is_expiring_soon(self):
        if not self.expires_at or self.is_expired:
            return False
        now = timezone.now()
        return now <= self.expires_at <= now + timezone.timedelta(days=1)


class PrivateFile(FilePreviewMixin, models.Model):
    sender = models.ForeignKey(
        User, related_name='sent_files',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User, related_name='received_files',
        on_delete=models.CASCADE
    )
    file = models.FileField(
        upload_to='private_files/',
        validators=[validate_file_size, validate_file_type]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files'
    )

    class Meta:
        verbose_name = "Şahsy faýl"
        verbose_name_plural = "Şahsy faýllar"

    def __str__(self):
        return f"{self.sender} → {self.receiver}"

    def delete_expired_file(self):
        if self.is_file_expired() and not self.is_expired:
            self.file.delete(save=False)
            self.is_expired = True
            self.save(update_fields=['file', 'is_expired', 'updated_at'])


class ClassFile(FilePreviewMixin, models.Model):
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to='class_files/', validators=[validate_file_size, validate_file_type])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Topar faýly"
        verbose_name_plural = "Topar faýllary"

    def __str__(self):
        return f"{self.classroom} - {self.file.name}"

    def delete_expired_file(self):
        if self.is_file_expired() and not self.is_expired:
            self.file.delete(save=False)
            self.is_expired = True
            self.save(update_fields=['file', 'is_expired', 'updated_at'])
class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('file', 'Faýl'),
        ('expiry', 'Möhlet'),
        ('quota', 'Kwota'),
        ('system', 'Ulgam'),
    ]
    LEVEL_CHOICES = [
        ('info', 'Maglumat'),
        ('warning', 'Duýduryş'),
        ('danger', 'Howply'),
        ('success', 'Üstünlik'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Duýduryş"
        verbose_name_plural = "Duýduryşlar"

    def __str__(self):
        return f"{self.user} - {self.title}"


class FileActivity(models.Model):
    ACTION_CHOICES = [
        ('upload', 'Ýükleme'),
        ('download', 'Göçürme'),
        ('preview', 'Görmek'),
        ('update', 'Üýtgetme'),
        ('delete', 'Pozma'),
        ('auto_delete', 'Awto-pozma'),
    ]
    FILE_TYPE_CHOICES = [
        ('private', 'Şahsy'),
        ('class', 'Topar'),
    ]

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='file_activities',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    private_file = models.ForeignKey(
        PrivateFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
    )
    class_file = models.ForeignKey(
        ClassFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
    )
    description = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Faýl hereketi"
        verbose_name_plural = "Faýl hereketleri"

    @property
    def file_name(self):
        if self.private_file:
            return self.private_file.filename
        if self.class_file:
            return self.class_file.filename
        return self.description or 'Faýl'

    def __str__(self):
        return f"{self.get_action_display()} - {self.file_name}"


class Assignment(models.Model):
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_assignments',
    )
    attachment = models.FileField(
        upload_to='assignments/',
        validators=[validate_file_size, validate_file_type],
        null=True,
        blank=True,
    )
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['due_date', '-created_at']
        verbose_name = "Tabşyryk"
        verbose_name_plural = "Tabşyryklar"

    @property
    def is_overdue(self):
        return timezone.now() > self.due_date

    @property
    def attachment_name(self):
        return os.path.basename(self.attachment.name) if self.attachment else ''

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_submissions',
    )
    file = models.FileField(
        upload_to='assignment_submissions/',
        validators=[validate_file_size, validate_file_type],
    )
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']
        verbose_name = "Tabşyryk jogaby"
        verbose_name_plural = "Tabşyryk jogaplary"

    @property
    def is_late(self):
        return self.submitted_at > self.assignment.due_date

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else ''

    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"


class NoticeBoardPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notice_posts',
    )
    attachment = models.FileField(
        upload_to='notice_board/',
        validators=[validate_file_size, validate_file_type],
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = "Bildiriş"
        verbose_name_plural = "Bildirişler"

    @property
    def attachment_name(self):
        return os.path.basename(self.attachment.name) if self.attachment else ''

    def __str__(self):
        return self.title


def create_notification(user, title, message, category='system', level='info', link='', is_system=False, once_per_day=False):
    if not user:
        return None
    queryset = Notification.objects.filter(
        user=user,
        title=title,
        message=message,
        category=category,
        created_at__date=timezone.localdate(),
    )
    if once_per_day and queryset.exists():
        return queryset.first()
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        category=category,
        level=level,
        link=link,
        is_system=is_system,
    )


def log_file_activity(action, file_type, actor=None, private_file=None, class_file=None, description='', ip_address=None):
    return FileActivity.objects.create(
        actor=actor,
        action=action,
        file_type=file_type,
        private_file=private_file,
        class_file=class_file,
        description=description,
        ip_address=ip_address,
    )


def _notify_private_file_expiry(private_file, title, message, level='warning'):
    users = {private_file.sender, private_file.receiver}
    for user in users:
        create_notification(
            user=user,
            title=title,
            message=message,
            category='expiry',
            level=level,
            link='/files/inbox/' if user == private_file.receiver else '/files/my-files/',
            is_system=True,
            once_per_day=True,
        )


def _notify_class_file_expiry(class_file, title, message, level='warning'):
    classroom_users = class_file.classroom.user_set.all()
    for user in classroom_users:
        create_notification(
            user=user,
            title=title,
            message=message,
            category='expiry',
            level=level,
            link='/files/class/',
            is_system=True,
            once_per_day=True,
        )


def generate_quota_alerts():
    from accounts.models import User as AccountUser

    for user in AccountUser.objects.filter(is_active=True):
        usage = user.get_storage_percentage()
        if usage >= 80:
            create_notification(
                user=user,
                title='Saklaýyş çägi dolmaga golaýlady',
                message=f"Siziň kwotaňyz {usage}% ulanyldy.",
                category='quota',
                level='warning' if usage < 95 else 'danger',
                link='/accounts/profile/',
                is_system=True,
                once_per_day=True,
            )


def generate_assignment_alerts():
    upcoming_assignments = Assignment.objects.filter(
        is_active=True,
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timezone.timedelta(days=1),
    )
    for assignment in upcoming_assignments:
        for student in assignment.classroom.user_set.all():
            create_notification(
                user=student,
                title='Tabşyrygyň möhleti golaýlady',
                message=f'"{assignment.title}" tabşyrygyny tabşyrmagyň möhleti tizden gutarýar.',
                category='expiry',
                level='warning',
                link='/files/assignments/',
                is_system=True,
                once_per_day=True,
            )


def run_file_lifecycle_checks():
    now = timezone.now()
    deleted_count = 0
    soon_count = 0

    expiring_private = PrivateFile.objects.filter(
        expires_at__isnull=False,
        expires_at__gt=now,
        expires_at__lte=now + timezone.timedelta(days=1),
        is_expired=False,
    )
    for private_file in expiring_private:
        soon_count += 1
        _notify_private_file_expiry(
            private_file,
            title='Şahsy faýlyň möhleti gutarmaga golaý',
            message=f'"{private_file.filename}" faýlynyň möhleti tizden gutarýar.',
            level='warning',
        )

    expiring_class = ClassFile.objects.filter(
        expires_at__isnull=False,
        expires_at__gt=now,
        expires_at__lte=now + timezone.timedelta(days=1),
        is_expired=False,
    )
    for class_file in expiring_class:
        soon_count += 1
        _notify_class_file_expiry(
            class_file,
            title='Topar faýlynyň möhleti gutarmaga golaý',
            message=f'"{class_file.filename}" faýlynyň möhleti tizden gutarýar.',
            level='warning',
        )

    expired_private = PrivateFile.objects.filter(
        expires_at__lt=now,
        is_expired=False,
    )
    for private_file in expired_private:
        filename = private_file.filename
        private_file.delete_expired_file()
        deleted_count += 1
        _notify_private_file_expiry(
            private_file,
            title='Şahsy faýl awtomatiki pozuldy',
            message=f'"{filename}" faýlynyň möhleti gutaryp, ulgam tarapyndan pozuldy.',
            level='danger',
        )
        log_file_activity(
            action='auto_delete',
            file_type='private',
            actor=None,
            private_file=private_file,
            description=f'{filename} awtomatiki pozuldy.',
        )

    expired_class = ClassFile.objects.filter(
        expires_at__lt=now,
        is_expired=False,
    )
    for class_file in expired_class:
        filename = class_file.filename
        class_file.delete_expired_file()
        deleted_count += 1
        _notify_class_file_expiry(
            class_file,
            title='Topar faýly awtomatiki pozuldy',
            message=f'"{filename}" faýlynyň möhleti gutaryp, ulgam tarapyndan pozuldy.',
            level='danger',
        )
        log_file_activity(
            action='auto_delete',
            file_type='class',
            actor=None,
            class_file=class_file,
            description=f'{filename} awtomatiki pozuldy.',
        )

    generate_quota_alerts()
    generate_assignment_alerts()
    return {
        'expiring_soon': soon_count,
        'deleted': deleted_count,
    }