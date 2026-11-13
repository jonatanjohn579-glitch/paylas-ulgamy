from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, ClassRoom

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_image']

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, ClassRoom

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_image']


class RegisterForm(UserCreationForm):
    # Roly saýlamak üçin select field goşýarys
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES, # Modelde bar bolan role choices (Talyp, Mugallym, Admin h.b.)
        label="Ulgamdaky rolyňyz",
        initial='student',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        empty_label="Toparyňy saýla",
        required=False, # Eger mugallym bolsa classroom hökman däl bolup biler
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'role', 'classroom']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user