from django.urls import path

from . import views

app_name = 'extensions'

urlpatterns = [
    path('', views.student_id, name='student-id'),
    path('<int:student_id>/', views.course, name='course'),
    path('<int:student_id>/<int:course_canvas_id>/', views.assignment, name='assignment'),
    path('success/', views.success, name='success'),
]