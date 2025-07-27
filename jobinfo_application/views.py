import requests
import xml.etree.ElementTree as ET
from openai import OpenAI
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
from django.contrib import messages
from django.utils import timezone
from .models import (
    JobApplication, Document, UserProfile, JobType,
    InterviewLog, EntrySheet
)
from .forms import (
    JobApplicationForm, DocumentForm, SignUpForm, UserProfileForm,
    InterviewLogForm, EntrySheetQuestionForm, EntrySheetAnswerForm
)



# ユーザー

def signup_view(request):
    """ユーザー登録（即時有効化・自動ログイン）"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ユーザー登録が完了しました。ようこそ！')
            return redirect('application-list')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def profile_edit_view(request):
    """プロフィール編集"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'プロフィールを更新しました。')
            return redirect('application-list')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'jobinfo_application/profile_form.html', {'form': form})

# 応募情報 

@login_required
def application_list(request):
    """応募情報の一覧"""
    applications = JobApplication.objects.filter(user=request.user).order_by('-applied_at')
    context = {'applications': applications}
    return render(request, 'jobinfo_application/jobapplication_list.html', context)


@login_required
def application_detail(request, pk):
    """応募情報の詳細"""
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    context = {
        'job_application': application,
        'document_form': DocumentForm(),
        'interview_log_form': InterviewLogForm(),
        'es_question_form': EntrySheetQuestionForm(),
    }
    return render(request, 'jobinfo_application/jobapplication_detail.html', context)


def _handle_job_types(form, application_instance):
    """自由記述の職種カテゴリを処理するヘルパー関数"""
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
    """応募情報の新規作成"""
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
    context = {'form': form, 'all_job_types': JobType.objects.all()}
    return render(request, 'jobinfo_application/jobapplication_form.html', context)


@login_required
def application_update(request, pk):
    """応募情報の更新"""
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
    context = {'form': form, 'all_job_types': JobType.objects.all()}
    return render(request, 'jobinfo_application/jobapplication_form.html', context)


@login_required
def application_delete(request, pk):
    """応募情報の削除"""
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        application.delete()
        messages.success(request, '応募情報を削除しました。')
        return redirect('application-list')
    return render(request, 'jobinfo_application/jobapplication_confirm_delete.html', {'object': application})


@login_required
def add_document(request, pk):
    """書類のアップロード"""
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.job_application = application
            document.save()
            messages.success(request, '書類をアップロードしました。')
    return redirect('application-detail', pk=pk)


# 面接ログ 

@login_required
def interview_log_create(request, job_app_pk):
    """面接ログの新規作成"""
    job_application = get_object_or_404(JobApplication, pk=job_app_pk, user=request.user)
    if request.method == 'POST':
        form = InterviewLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.job_application = job_application
            log.save()
            messages.success(request, '面接ログを登録しました。')
            return redirect('application-detail', pk=job_app_pk)
    else:
        form = InterviewLogForm()
    context = {'form': form, 'job_application': job_application}
    return render(request, 'jobinfo_application/interview_log_form.html', context)


@login_required
def interview_log_update(request, pk):
    """面接ログの更新"""
    log = get_object_or_404(InterviewLog, pk=pk, job_application__user=request.user)
    job_application = log.job_application
    if request.method == 'POST':
        form = InterviewLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            messages.success(request, '面接ログを更新しました。')
            return redirect('application-detail', pk=job_application.pk)
    else:
        form = InterviewLogForm(instance=log)
    context = {'form': form, 'job_application': job_application}
    return render(request, 'jobinfo_application/interview_log_form.html', context)


@login_required
def interview_log_delete(request, pk):
    """面接ログの削除"""
    log = get_object_or_404(InterviewLog, pk=pk, job_application__user=request.user)
    job_application = log.job_application
    if request.method == 'POST':
        log.delete()
        messages.success(request, '面接ログを削除しました。')
        return redirect('application-detail', pk=job_application.pk)
    return render(request, 'jobinfo_application/interview_log_confirm_delete.html', {'log': log})


# ES作成支援


@login_required
def es_question_create(request, job_app_pk):
    """ES設問の新規作成"""
    job_application = get_object_or_404(JobApplication, pk=job_app_pk, user=request.user)
    if request.method == 'POST':
        form = EntrySheetQuestionForm(request.POST)
        if form.is_valid():
            es = form.save(commit=False)
            es.job_application = job_application
            es.save()
            return redirect('es-detail', pk=es.pk)
    else:
        form = EntrySheetQuestionForm()
    
    context = {
        'form': form,
        'job_application': job_application
    }

    return render(request, 'jobinfo_application/es_question_form.html', context)


@login_required
def es_detail_view(request, pk):
    """ES設問の詳細・回答編集"""
    entry_sheet = get_object_or_404(EntrySheet, pk=pk, job_application__user=request.user)
    form = EntrySheetAnswerForm(instance=entry_sheet)
    context = {'entry_sheet': entry_sheet, 'form': form}
    return render(request, 'jobinfo_application/es_detail.html', context)


@login_required
def es_answer_update(request, pk):
    """ESの回答下書きを保存"""
    entry_sheet = get_object_or_404(EntrySheet, pk=pk, job_application__user=request.user)
    if request.method == 'POST':
        form = EntrySheetAnswerForm(request.POST, instance=entry_sheet)
        if form.is_valid():
            form.save()
            messages.success(request, '回答の下書きを保存しました。')
    return redirect('es-detail', pk=pk)


@login_required
def es_question_delete(request, pk):
    """ES設問の削除"""
    entry_sheet = get_object_or_404(EntrySheet, pk=pk, job_application__user=request.user)
    job_app_pk = entry_sheet.job_application.pk
    if request.method == 'POST':
        entry_sheet.delete()
        messages.success(request, 'ES設問を削除しました。')
        return redirect('application-detail', pk=job_app_pk)
    return render(request, 'jobinfo_application/es_confirm_delete.html', {'entry_sheet': entry_sheet})


@login_required
def generate_es_answer_view(request, pk):
    """ES設問に対する回答をAIが生成"""
    entry_sheet = get_object_or_404(EntrySheet, pk=pk, job_application__user=request.user)
    job_application = entry_sheet.job_application
    user_profile = request.user.profile
    
    user_info = f"スキル: {user_profile.skills}\n経験: {user_profile.experience}\n自己PR: {user_profile.self_pr}"
    company_info = f"企業名: {job_application.company_name}\n経営理念: {job_application.corporate_philosophy}\n求める人物像: {job_application.ideal_candidate}\n業務内容: {job_application.job_description}"

    if request.method == 'POST':
        prompt = f"""あなたは優秀なキャリアアドバイザーです。以下のES設問に対し、候補者のプロフィールと企業の情報を最大限に活用し、説得力のある回答ドラフトを400字程度で作成してください。

    # ES設問
    {entry_sheet.question}

    # 候補者のプロフィール情報
    {user_info}

    # 企業の情報
    {company_info}

    # 作成する回答ドラフト
    """
        try:
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  
                messages=[
                    {"role": "system", "content": "あなたは優秀なキャリアアドバイザーです。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            ai_draft = response.choices[0].message.content.strip()

            if ai_draft: 
                entry_sheet.ai_draft = ai_draft
                entry_sheet.save()
                messages.success(request, 'AIによる回答の提案を生成しました。')
            else:
                messages.warning(request, 'AIが空の回答を返しました。再度お試しください。')
            
        except Exception as e:
            messages.error(request, f"AIの呼び出し中にエラーが発生しました: {e}")
    
    return redirect('es-detail', pk=pk)


# 外部API連携ビュー

def search_company_view(request):
    """Wikidata APIを呼び出し、企業名を検索して候補を返すAPIビュー"""
    company_name = request.GET.get('name', '')
    if len(company_name) < 2:
        return JsonResponse([], safe=False)
    api_url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbsearchentities", "format": "json", "language": "ja", "type": "item", "search": company_name}
    try:
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        candidates = [{'name': result.get('label')} for result in data.get("search", [])]
        return JsonResponse(candidates, safe=False)
    except requests.exceptions.RequestException:
        return JsonResponse({'error': 'API request failed'}, status=500)

@login_required
def search_jobtype_view(request):
    """データベース内の既存の職種カテゴリを検索して候補を返すAPIビュー"""
    query = request.GET.get('term', '')
    job_types = JobType.objects.filter(name__icontains=query)[:10]
    results = [jt.name for jt in job_types]
    return JsonResponse(results, safe=False)