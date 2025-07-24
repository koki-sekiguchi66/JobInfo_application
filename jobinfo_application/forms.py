from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import JobApplication, Document
from .models import UserProfile

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="メールアドレス",
        help_text="パスワードリセットなどに使用します。"
    )

    class Meta:
        model = User
        fields = ('username', 'email')


class JobApplicationForm(forms.ModelForm):
    job_types_input = forms.CharField(
        required=False,
        label="職種カテゴリ",
        help_text="カンマ区切りで入力してください。（例: バックエンド, フロントエンド）"
    )

    class Meta:
        model = JobApplication
        fields = [
            'company_name', 'job_title', 'status', 'job_types_input',
            'corporate_philosophy', 'ideal_candidate', 'job_description',
            'next_action', 'next_action_date', 'notes'
        ]
        
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'next_action': forms.TextInput(attrs={'class': 'form-control'}),
            'next_action_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'uploaded_file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'uploaded_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['skills', 'experience', 'self_pr']
        widgets = {
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'self_pr': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        }