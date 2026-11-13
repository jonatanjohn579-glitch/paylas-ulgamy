from django import forms
from .models import (
    Assignment,
    AssignmentSubmission,
    ClassFile,
    Folder,
    NoticeBoardPost,
    PrivateFile,
)

class PrivateFileForm(forms.ModelForm):
    expiry_days = forms.TypedChoiceField(
        label='Faýlyň möhleti',
        choices=[
            (0, 'Möhletsiz'),
            (1, '1 gün'),
            (7, '7 gün'),
            (30, '30 gün'),
        ],
        coerce=int,
        initial=0,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = PrivateFile
        fields = ['file', 'comment']
        help_texts = {
            'file': 'Rugsat edilen görnüşler: PDF, suratlar, dokumentler'} # sender ve receiver view-de berilýär

class ClassFileForm(forms.ModelForm):
    expiry_days = forms.TypedChoiceField(
        label='Faýlyň möhleti',
        choices=[
            (0, 'Möhletsiz'),
            (1, '1 gün'),
            (7, '7 gün'),
            (30, '30 gün'),
        ],
        coerce=int,
        initial=0,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = ClassFile
        fields = ['file', 'comment']  # classroom ve uploaded_by view-de berilýär

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'parent']  # parent islege görä
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Papka ady'}),
        }


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        label='Soňky tabşyrmaly wagt',
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Assignment
        fields = ['classroom', 'title', 'description', 'attachment', 'due_date', 'is_active']
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tabşyryk ady'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tabşyryk düşündirişi'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['file', 'comment']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Düşündiriş ýa-da bellik'}),
        }


class NoticeBoardPostForm(forms.ModelForm):
    class Meta:
        model = NoticeBoardPost
        fields = ['title', 'content', 'attachment', 'is_pinned', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bildiriş sözbaşy'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Bildiriş mazmuny'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
