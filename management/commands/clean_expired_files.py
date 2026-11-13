from django.core.management.base import BaseCommand
from files.models import run_file_lifecycle_checks

class Command(BaseCommand):
    def handle(self, *args, **options):
        result = run_file_lifecycle_checks()
        self.stdout.write(
            self.style.SUCCESS(
                f"Barlag tamamlandy. Golaý möhletli: {result['expiring_soon']}, awto-pozulan: {result['deleted']}"
            )
        )
