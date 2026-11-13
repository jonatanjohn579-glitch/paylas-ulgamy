from .models import run_file_lifecycle_checks


class FileLifecycleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith('/media/'):
            run_file_lifecycle_checks()
        return self.get_response(request)
