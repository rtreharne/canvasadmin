from django.contrib import admin
from .forms import ModulesSearchForm, ModulesUpdateForm
from django.urls import path
from .models import Module
from accounts.models import UserProfile
from django.shortcuts import render, redirect
from .tasks import get_modules, task_update_modules
from core.models import Course
from django.utils.html import format_html

class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "module_link",
        "course",
        "unlock_at",
        "published"
    )

    list_filter=(
        "name",
    )

    actions = ["update_modules"]

    def module_link(self, obj):
        return format_html('<a target="_blank" href="{}/courses/{}/modules/{}">{}</a>'.format(
            obj.course.course_department.CANVAS_API_URL,
            obj.course.course_id,
            obj.module_id,
            obj.name)
            )
       
    change_list_template = "modules/modules_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('find-modules/', self.find_modules),
            path('update-modules/', self.update_modules),
        ]
        return my_urls + urls

    def find_modules(self, request):
        if request.method == "POST":
            search_string = request.POST.get("search")
            department = UserProfile.objects.get()
            course_ids = [x.course_id for x in Course.objects.all()]
            user = UserProfile.objects.get(user__username=request.user.username)
            department = user.department
            course_ids = [x.course_id for x in Course.objects.filter(course_department=department)]
            get_modules.delay(request.user.username, course_ids, search_string)

            self.message_user(request, "Your request has been submitted. Your modules will appear shortly. Keep refreshing.")
            return redirect("..")
        form = ModulesSearchForm()
        payload = {"form": form}
        return render(
            request, "modules/modules_form.html", payload
        )
    
    def update_modules(self, request, queryset):
        if 'apply' in request.POST:
            print(request.POST)
            module_pks = request.POST.get("_selected_action")
            unlock_date = request.POST.get("unlock_date", None)
            unlock_time = request.POST.get("unlock_time", None)
            publish = request.POST.get("force_publish", None)
            if publish != None:
                publish = True

            time_string = unlock_date + "T" + unlock_time + ":00Z"
            module_ids = [x.id for x in queryset]
            task_update_modules.delay(request.user.username, module_ids, time_string, publish=publish)
            self.message_user(request, "Your request has been submitted. Your modules will update shortly. Keep refreshing.")
            return redirect(".")
        form = ModulesUpdateForm()
        payload = {'form': form, 'modules': queryset}
        return render(
            request, "modules/modules_update_form.html", payload
        )

    def get_queryset(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        queryset = Module.objects.filter(course__course_department=user_profile.department)
        return queryset

admin.site.register(Module, ModuleAdmin)