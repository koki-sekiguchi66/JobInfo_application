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
    class Meta:
        model = JobApplication
        fields = ['company_name', 'job_title', 'status', 'next_action', 'next_action_date', 'job_description', 'notes']
        widgets = {'next_action_date': forms.DateInput(attrs={'type': 'date'})}

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'uploaded_file']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['skills', 'experience', 'self_pr']