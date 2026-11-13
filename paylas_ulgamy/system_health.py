"""
System health monitoring utilities for Paylas Ulgamy
"""
import shutil
import os
import psutil
from pathlib import Path
from django.conf import settings


def get_disk_usage():
    """
    Get disk usage statistics
    Returns: {
        'total': total bytes,
        'used': used bytes,
        'free': free bytes,
        'percent': percentage used,
        'media_used': bytes used in media folder
    }
    """
    disk_stat = shutil.disk_usage(settings.MEDIA_ROOT)
    
    # Calculate media folder usage
    media_used = 0
    for dirpath, dirnames, filenames in os.walk(settings.MEDIA_ROOT):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                media_used += os.path.getsize(filepath)
            except (OSError, IOError):
                pass
    
    return {
        'total': disk_stat.total,
        'used': disk_stat.used,
        'free': disk_stat.free,
        'percent': round((disk_stat.used / disk_stat.total) * 100, 2),
        'media_used': media_used,
    }


def get_memory_usage():
    """
    Get system memory usage
    Returns: {
        'total': total MB,
        'used': used MB,
        'available': available MB,
        'percent': percentage used
    }
    """
    try:
        memory = psutil.virtual_memory()
        return {
            'total': round(memory.total / (1024*1024), 2),
            'used': round(memory.used / (1024*1024), 2),
            'available': round(memory.available / (1024*1024), 2),
            'percent': memory.percent,
        }
    except Exception:
        return None


def get_cpu_usage():
    """
    Get CPU usage percentage
    """
    try:
        return round(psutil.cpu_percent(interval=1), 2)
    except Exception:
        return None


def get_system_health():
    """
    Get overall system health status
    Returns health check data with warnings
    """
    health = {
        'status': 'OK',
        'warnings': [],
        'disk': get_disk_usage(),
        'memory': get_memory_usage(),
        'cpu': get_cpu_usage(),
    }
    
    # Check disk usage
    if health['disk']['percent'] > 90:
        health['status'] = 'CRITICAL'
        health['warnings'].append(f"CRITICAL: Disk space 90% full!")
    elif health['disk']['percent'] > 75:
        health['status'] = 'WARNING'
        health['warnings'].append(f"WARNING: Disk space 75% full!")
    
    # Check memory usage
    if health['memory']:
        if health['memory']['percent'] > 90:
            health['warnings'].append(f"WARNING: Memory 90% full!")
        elif health['memory']['percent'] > 80:
            health['warnings'].append(f"NOTICE: Memory 80% full!")
    
    # Check CPU usage
    if health['cpu'] and health['cpu'] > 80:
        health['warnings'].append(f"NOTICE: High CPU usage ({health['cpu']}%)")
    
    return health


def format_bytes(bytes_size):
    """
    Convert bytes to human-readable format
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"
