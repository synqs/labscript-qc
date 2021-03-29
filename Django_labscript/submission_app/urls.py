from django.urls import path
from submission_app import views

urlpatterns = [
    path('get_config/', views.get_config, name='get_config'),
    path('post_job/', views.post_job, name='post_job'),
    path('get_job_status/', views.get_job_status, name='get_job_status'),
    path('get_job_result/', views.get_job_result, name='get_job_result'),
]
