from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import JobApplication, Document, UserProfile, JobType

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="メールアドレス",
        help_text="パスワードリセットなどに使用します。"
    )

    class Meta:
        model = User
        fields = ('username', 'email')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
        return user



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

        def __init__(self, *args, **kwargs):
            """
            フォームの初期化
            """
            super().__init__(*args, **kwargs)
            if self.instance and self.instance.pk:
                self.fields['job_types_input'].initial = ', '.join([job.name for job in self.instance.job_types.all()])



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