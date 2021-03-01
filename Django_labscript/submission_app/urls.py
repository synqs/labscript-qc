from django.urls import path
from submission_app import views

urlpatterns = [
    path('config/', views.config, name='config'),
    path('upload/', views.upload, name='upload'),
    path('check_shot_status/', views.check_shot_status, name='check_shot_status'),
]
