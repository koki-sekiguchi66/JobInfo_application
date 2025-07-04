from django.urls import path
from . import views

urlpatterns = [
    path('accounts/signup/', views.signup_view, name='signup'),
    
    # path('accounts/', include('django.contrib.auth.urls')), 
    path('', views.application_list, name='application-list'),
    path('application/<int:pk>/', views.application_detail, name='application-detail'),
    path('application/new/', views.application_create, name='application-create'),
    path('application/<int:pk>/update/', views.application_update, name='application-update'),
    path('application/<int:pk>/delete/', views.application_delete, name='application-delete'),
    path('application/<int:pk>/add_document/', views.add_document, name='add-document'),
    path('application/<int:pk>/generate_draft/', views.generate_draft_view, name='generate-draft'),
    path('profile/', views.profile_edit_view, name='profile-edit'),
]