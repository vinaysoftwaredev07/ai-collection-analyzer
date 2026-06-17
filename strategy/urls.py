from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('borrower/add/', views.borrower_create_view, name='borrower_add'),
    path('borrower/parse_document/', views.parse_document_view, name='parse_document'),
    path('borrower/<int:pk>/', views.borrower_detail_view, name='borrower_detail'),
    path('borrower/<int:pk>/document/', views.serve_document, name='serve_document'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='strategy/login.html',
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
