from django.urls import path

from . import views

app_name = 'extensions'

urlpatterns = [
    path('elp/', views.student_id, name='student-id'),
    path('elp/<int:student_id>/', views.course, name='course'),
    path('elp/<int:student_id>/<int:course_canvas_id>/', views.assignment, name='assignment'),
    path('elp/success/', views.success, name='success'),
    path('elp/confirm/<uuid:confirmation_id>/', views.confirmation, name='confirmation'),
]