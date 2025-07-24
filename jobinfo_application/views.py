import requests
import xml.etree.ElementTree as ET
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login 
from .models import JobApplication, Document, UserProfile, JobType
from .forms import JobApplicationForm, DocumentForm, SignUpForm, UserProfileForm 
from django.utils import timezone

import openai


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
    upcoming_events = JobApplication.objects.filter(user=request.user, 
                                                    next_action_date__gte=timezone.now().date()).order_by('next_action_date')
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

def search_company_view(request):
    """Wikidata APIを呼び出し、企業名を検索して候補を返す"""
    company_name = request.GET.get('name', '')
    if len(company_name) < 2:
        return JsonResponse([], safe=False)

    api_url = "https://www.wikidata.org/w/api.php"
    
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "ja",  
        "type": "item",
        "search": company_name
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        candidates = []
        if "search" in data:
            for result in data["search"]:
                candidates.append({'name': result.get('label')})
        
        return JsonResponse(candidates, safe=False)
    
    except requests.exceptions.RequestException:
        return JsonResponse({'error': 'API request failed'}, status=500)
    
@login_required
def search_jobtype_view(request):
    query = request.GET.get('term', '')
    job_types = JobType.objects.filter(name__icontains=query)[:10]
    results = [job.name for job in job_types]
    return JsonResponse(results, safe=False)

def _handle_job_types(form, application_instance):
    job_types_str = form.cleaned_data.get('job_types_input', '')
    application_instance.job_types.clear()
    
    if job_types_str:
        job_type_names = [name.strip() for name in job_types_str.split(',')]
        for name in job_type_names:
            if name:
                job_type, _ = JobType.objects.get_or_create(name=name)
                application_instance.job_types.add(job_type)

@login_required
def application_create(request):
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            _handle_job_types(form, application)
            return redirect('application-detail', pk=application.pk)
    else:
        form = JobApplicationForm()
        context = {
            'form': form,
            'all_job_types': JobType.objects.all(),
        }
    return render(request, 'jobinfo_application/jobapplication_form.html', context)

@login_required
def application_update(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save(commit=False)
            application.save()
            _handle_job_types(form, application)
            return redirect('application-detail', pk=application.pk)
    else:
        form = JobApplicationForm(instance=application)
        context = {
        'form': form,
        'all_job_types': JobType.objects.all(),
    }
        
    return render(request, 'jobinfo_application/jobapplication_form.html', context)

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
    job_types_str = ", ".join([job_type.name for job_type in application.job_types.all()])
    company_info = f"""
        # 企業名
        {application.company_name}

        # 職種カテゴリ
        {job_types_str}

        # 経営理念・ビジョン
        {application.corporate_philosophy}

        # 企業の求める人物像
        {application.ideal_candidate}

        # 業務内容
        {application.job_description}
        """
    
    user_profile = request.user.profile        
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
        if not application.job_description:
            generated_text = "エラー: この応募情報に、分析対象となる求人情報が登録されていません。"
        else:
            prompt = f"""あなたは優秀なキャリアアドバイザーです。以下の情報に基づいて、志望動機のドラフトを作成してください。
                候補者の経験やスキル、強みが、企業の求める人物像にどのように合致するかを具体的に記述してください。

                # 企業の詳細情報
                {company_info}

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