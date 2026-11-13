from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import ProfileImageForm,RegisterForm
from .models import User, ClassRoom
from django.db.models import Q 
from django.contrib import messages
from django.core.paginator import Paginator

# Create your views here.
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileImageForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def student_list(request):
    # Ähli okuwçylar (özüňden başga)
    students_list = User.objects.exclude(id=request.user.id).exclude(classroom=None)

    # Gözleg we filter
    query = request.GET.get('q')
    class_id = request.GET.get('class')

    if query:
        students_list = students_list.filter(username__icontains=query)

    if class_id:
        students_list = students_list.filter(classroom_id=class_id)

    # PAGINATION: sahypada 20 okuwçy
    paginator = Paginator(students_list, 20)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)  # pagination obyekti

    classes = ClassRoom.objects.all()

    context = {
        'students': students,  # pagination obyekti
        'classes': classes,
        'query': query,
        'selected_class': class_id
    }

    return render(request, 'accounts/student_list.html', context)
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    """Logout via GET or POST and redirect to login."""
    if request.method in ('POST', 'GET'):
        logout(request)
    return redirect('login')
