from django.urls import path
from . import views

urlpatterns = [
    path('api/search-company/', views.search_company_view, name='search-company'),
    path('api/search-jobtypes/', views.search_jobtype_view, name='search-jobtype'),
    path('accounts/signup/', views.signup_view, name='signup'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_view, name='activate'),
    path('activation-sent/', views.account_activation_sent_view, name='account_activation_sent'),
    path('', views.application_list, name='application-list'),
    path('application/<int:pk>/', views.application_detail, name='application-detail'),
    path('application/new/', views.application_create, name='application-create'),
    path('application/<int:pk>/update/', views.application_update, name='application-update'),
    path('application/<int:pk>/delete/', views.application_delete, name='application-delete'),
    path('application/<int:pk>/add_document/', views.add_document, name='add-document'),
    path('application/<int:pk>/generate_draft/', views.generate_draft_view, name='generate-draft'),
    path('profile/', views.profile_edit_view, name='profile-edit'),
]