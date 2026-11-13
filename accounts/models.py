from django.contrib.auth.models import AbstractUser
from django.db import models

class ClassRoom(models.Model):
    name = models.CharField(max_length=10, unique=True)
    storage_quota = models.BigIntegerField(
        default=5 * 1024 * 1024 * 1024,  # 5 GB default
        help_text="Class storage quota in bytes"
    )

    def __str__(self):
        return self.name

    def get_storage_used(self):
        """Return total bytes used by files in this classroom."""
        # Local import to avoid circular imports at module import time
        from files.models import ClassFile

        total = 0
        for f in ClassFile.objects.filter(classroom=self):
            if f.file and hasattr(f.file, 'size') and f.file.size:
                total += f.file.size
        return total

    def has_space_for(self, size_bytes):
        """Check whether classroom has space for an upload of size_bytes."""
        return (self.get_storage_used() + size_bytes) <= self.storage_quota


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STUDENT, 'Student'),
    ]

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    profile_image = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )
    storage_quota = models.BigIntegerField(
        default=1073741824,  # 1GB in bytes
        help_text="Maximum storage allowed in bytes (default: 1GB)"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
    )

    def get_total_storage_used(self):
        """Calculate total storage used by this user"""
        from files.models import PrivateFile, ClassFile
        
        total = 0
        
        # Private files sent and received
        for f in self.sent_files.all():
            if f.file and hasattr(f.file, 'size'):
                total += f.file.size
        
        for f in self.received_files.all():
            if f.file and hasattr(f.file, 'size'):
                total += f.file.size
        
        # Class files uploaded
        for f in self.classfile_set.all():
            if f.file and hasattr(f.file, 'size'):
                total += f.file.size
        
        return total
    
    def get_remaining_storage(self):
        """Get remaining storage quota"""
        used = self.get_total_storage_used()
        return max(0, self.storage_quota - used)
    
    def get_storage_percentage(self):
        """Get storage usage as percentage"""
        used = self.get_total_storage_used()
        if self.storage_quota == 0:
            return 0
        return round((used / self.storage_quota) * 100, 2)
    
    def has_storage_available(self, file_size):
        """Check if user has storage for a file"""
        used = self.get_total_storage_used()
        return (used + file_size) <= self.storage_quota

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.ROLE_ADMIN

    @property
    def is_teacher_role(self):
        return self.is_admin_role or self.role == self.ROLE_TEACHER

    @property
    def is_student_role(self):
        return self.role == self.ROLE_STUDENT and not self.is_admin_role

    def __str__(self):
        return self.username
