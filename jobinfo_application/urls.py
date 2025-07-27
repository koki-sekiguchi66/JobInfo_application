from django.urls import path
from . import views



urlpatterns = [
    # API
    path('api/search-company/', views.search_company_view, name='search-company'),
    path('api/search-jobtypes/', views.search_jobtype_view, name='search-jobtype'),
    
    # 認証
    path('signup/', views.signup_view, name='signup'),
    
    # 応募情報
    path('', views.application_list, name='application-list'),
    path('application/<int:pk>/', views.application_detail, name='application-detail'),
    path('application/new/', views.application_create, name='application-create'),
    path('application/<int:pk>/update/', views.application_update, name='application-update'),
    path('application/<int:pk>/delete/', views.application_delete, name='application-delete'),
    
    # 書類
    path('application/<int:pk>/add_document/', views.add_document, name='add-document'),
    
    # プロフィール
    path('profile/', views.profile_edit_view, name='profile-edit'),

    # 面接ログ
    path('application/<int:job_app_pk>/log/new/', views.interview_log_create, name='interview-log-create'), 
    path('log/<int:pk>/update/', views.interview_log_update, name='interview-log-update'),
    path('log/<int:pk>/delete/', views.interview_log_delete, name='interview-log-delete'),
    
    # ES作成支援
    path('application/<int:job_app_pk>/es/new/', views.es_question_create, name='es-question-create'), 
    path('es/<int:pk>/', views.es_detail_view, name='es-detail'),
    path('es/<int:pk>/update/', views.es_answer_update, name='es-answer-update'),
    path('es/<int:pk>/delete/', views.es_question_delete, name='es-question-delete'),
    path('es/<int:pk>/generate/', views.generate_es_answer_view, name='es-generate-answer'),

]