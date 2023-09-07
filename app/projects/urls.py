from django.urls import path
from django.contrib import admin

admin

from . import views

app_name = 'projects'

urlpatterns = [
    path("", views.index, name="index"),
    path("back/", views.back, name="back"),
    path("SVS", views.SVS, name="SVS"),
    path("staff_details/", views.staff_details, name="staff-details"),
    path("project_details/", views.project_details, name="project-details"),
    path("returning_staff/", views.returning_staff, name="returning-staff"),
    #path("staff_thanks/", views.staff_thanks, name="staff-thanks"),
    path("student_thanks/", views.student_thanks, name="student-thanks"),
    #path("download/", projects.views.download, name='download'),
    #path("download_student/", views.download_student, name='downlaod-student'),
    #path("download_staff/", projects.views.download_staff, name='download-staff'),
    #path("iacd_download/", projects.views.iacd_download, name='iacd-download'),
    path("student/", views.student, name='student'),
    path("<str:school>/student/", views.student, name='student'),
    path("tandc/", views.tandc, name='tandc'),
    path("privacy/", views.privacy, name='privacy'),
    #path("keywords_list/", projects.views.keywords_list, name='keywords-list'),
    #path("area_list/", projects.views.area_list, name='area-list'),
    #path("type_list/", projects.views.type_list, name='type-list'),
    path("staff_project/", views.staff_project, name='staff-project'),
    path("use_again/<id>", views.use_again, name='use-again'),
    path("edit_project/<id>", views.edit_project, name='edit-project'),
    path("admin/", admin.site.urls),
]