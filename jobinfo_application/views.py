import openai
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login 
from .models import JobApplication, Document
from .forms import JobApplicationForm, DocumentForm, SignUpForm 
from django.utils import timezone


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
def generate_draft_view(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    generated_text, user_skills = "", ""
    if request.method == 'POST':
        job_description = application.job_description
        user_skills = request.POST.get('user_skills', '')
        if not job_description:
            generated_text = "エラー: 求人情報が登録されていません。"
        else:
            prompt = f"""あなたは優秀なキャリアアドバイザーです。以下の情報に基づいて、志望動機のドラフトを作成してください。
# 企業の求人内容
{job_description}
# 候補者のスキルや経歴
{user_skills}
# 作成する志望動機"""
            try:
                openai.api_key = settings.OPENAI_API_KEY
                response = openai.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
                generated_text = response.choices[0].message.content.strip()
            except Exception as e:
                generated_text = f"エラー: {e}"
    context = {
        'application': application, 'documents': application.documents.all(), 'document_form': DocumentForm(),
        'generated_text': generated_text, 'submitted_skills': user_skills
    }
    return render(request, 'jobinfo_application/jobapplication_detail.html', context)