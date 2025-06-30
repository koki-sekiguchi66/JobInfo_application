import openai
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login 
from .models import JobApplication, Document
from .forms import JobApplicationForm, DocumentForm, SignUpForm 
from django.utils import timezone
from .models import UserProfile
from .forms import UserProfileForm


def signup_view(request):
    """ユーザー登録ビュー"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            return redirect('application-list') 
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def application_list(request):
    applications = JobApplication.objects.filter(user=request.user).order_by('-applied_at')
    upcoming_events = JobApplication.objects.filter(user=request.user, next_action_date__gte=timezone.now().date()).order_by('next_action_date')
    context = {'applications': applications, 'upcoming_events': upcoming_events}
    return render(request, 'jobinfo_application/jobapplication_list.html', context)

@login_required
def application_detail(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    context = {
        'application': application,
        'documents': application.documents.all(),
        'document_form': DocumentForm(),
    }
    return render(request, 'jobinfo_application/jobapplication_detail.html', context)

@login_required
def application_create(request):
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            return redirect('application-detail', pk=application.pk)
    else:
        form = JobApplicationForm()
    return render(request, 'jobinfo_application/jobapplication_form.html', {'form': form})

@login_required
def application_update(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            return redirect('application-detail', pk=application.pk)
    else:
        form = JobApplicationForm(instance=application)
    return render(request, 'jobinfo_application/jobapplication_form.html', {'form': form})

@login_required
def application_delete(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        application.delete()
        return redirect('application-list')
    return render(request, 'jobinfo_application/jobapplication_confirm_delete.html', {'object': application})

@login_required
def add_document(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.job_application = application
            document.save()
    return redirect('application-detail', pk=pk)


@login_required
def profile_edit_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('application-list') 
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'jobinfo_application/profile_form.html', {'form': form})

@login_required
def generate_draft_view(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    
    user_profile = request.user.profile
    
    job_description = application.job_description
    
    user_info = f"""
# スキル・資格
{user_profile.skills}

# 経験
{user_profile.experience}

# 自己PR
{user_profile.self_pr}
"""
    generated_text = ""
    if request.method == 'POST':
        if not job_description:
            generated_text = "エラー: この応募情報に、分析対象となる求人情報が登録されていません。"
        else:
            prompt = f"""あなたは優秀なキャリアアドバイザーです。以下の情報に基づいて、志望動機のドラフトを作成してください。候補者の経験やスキル、強みが、企業の求める人物像にどのように合致するかを具体的に記述してください。

# 企業の求人内容
{job_description}

# プロフィール情報
{user_info}

# 作成する志望動機
"""
            try:
                openai.api_key = settings.OPENAI_API_KEY
                response = openai.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                generated_text = response.choices[0].message.content.strip()
            except Exception as e:
                generated_text = f"エラー: {e}"
    
    context = {
        'application': application,
        'documents': application.documents.all(),
        'document_form': DocumentForm(),
        'generated_text': generated_text,
        'user_info_for_display': user_info
    }
    return render(request, 'jobinfo_application/jobapplication_detail.html', context)