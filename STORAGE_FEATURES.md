# Paylas Ulgamy - Setup & Installation

## Features Implemented

### 1. **Storage Quotas**
- Each user has a configurable storage quota (default: 1GB)
- Users can see their storage usage in their profile
- File uploads are blocked if storage limit is exceeded
- Admins can set individual quotas per user in Django admin

**Methods Available:**
- `User.get_total_storage_used()` - Total storage used by user
- `User.get_remaining_storage()` - Remaining quota
- `User.get_storage_percentage()` - Usage percentage
- `User.has_storage_available(file_size)` - Check before upload

### 2. **System Health Check**
- Monitor disk space usage
- Monitor system memory usage
- Monitor CPU usage
- Alert system for critical/warning states
- Display in admin dashboard

**System Health Status:**
- 🟢 **OK**: All systems normal
- 🟡 **WARNING**: Disk >75%, Memory >80%
- 🔴 **CRITICAL**: Disk >90%

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py migrate accounts 0002_user_storage_quota
```

### 3. Create Superuser (if not exists)
```bash
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

## Configuration

### Set Custom Storage Quotas
1. Go to Django Admin (`/admin`)
2. Click on "Users"
3. Edit a user
4. Scroll to "Storage Settings"
5. Set `storage_quota` in bytes (examples):
   - 1GB: 1073741824
   - 500MB: 536870912
   - 2GB: 2147483648

### Default Quota
- Current default: 1GB per user
- To change default, modify `accounts/models.py` User model

## Features

### User Benefits
✅ Track storage usage
✅ See remaining quota
✅ Clear error messages when quota exceeded
✅ Upload protection

### Admin Benefits
✅ Monitor system health
✅ View disk space usage
✅ Monitor memory and CPU
✅ Get warnings for critical conditions
✅ Configure per-user quotas
✅ See top storage users

## File Structure
```
paylas_ulgamy/
├── paylas_ulgamy/
│   ├── system_health.py       # NEW: System health monitoring
│   ├── views.py              # Updated: Added health check to admin
├── accounts/
│   ├── models.py             # Updated: Added storage_quota & methods
│   ├── admin.py              # Updated: Display storage info
│   ├── migrations/
│   │   └── 0002_user_storage_quota.py  # NEW: Migration
│   ├── templates/
│   │   └── profile.html      # Updated: Show storage info
├── files/
│   ├── views.py              # Updated: Check quota before upload
└── requirements.txt          # NEW: Dependencies
```

## Usage Examples

### In Templates
```django
<!-- Show user's storage usage -->
<p>Used: {{ request.user.get_total_storage_used|filesizeformat }}</p>
<p>Quota: {{ request.user.storage_quota|filesizeformat }}</p>
<p>Remaining: {{ request.user.get_remaining_storage|filesizeformat }}</p>
<p>Usage: {{ request.user.get_storage_percentage }}%</p>
```

### In Views
```python
# Check before allowing upload
if request.user.has_storage_available(file_size):
    # Save file
    file.save()
else:
    # Show error
    messages.error(request, "Storage quota exceeded!")
```

### System Health
```python
from paylas_ulgamy.system_health import get_system_health, format_bytes

health = get_system_health()
print(f"Disk: {health['disk']['percent']}% used")
print(f"Status: {health['status']}")  # OK, WARNING, or CRITICAL
```

## Troubleshooting

### psutil not installed
```bash
pip install psutil
```

### Migration errors
```bash
python manage.py makemigrations
python manage.py migrate
```

### Storage calculations incorrect
Clear Django cache and reload:
```bash
python manage.py shell
>>> from accounts.models import User
>>> User.objects.all().update(...)  # Force recalculation
```

## Future Enhancements
- [ ] Automatic cleanup of old files
- [ ] Storage quota warnings via email
- [ ] Graphical storage reports per class
- [ ] Tiered storage quotas by user role
- [ ] Archive large files to external storage
