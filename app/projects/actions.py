import csv
from django.http import HttpResponse
import datetime
from .forms import StudentForm

def export_project_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')

    # Create a timestamped filename
    filename = "%s-%s.csv" % (
        modeladmin.model._meta.verbose_name_plural,
        datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'

    writer = csv.writer(response)

    # Define fields manually
    fields = [
        'id', 
        'staff_username',
        'staff_surname',
        'staff_email',
        'project_area', 
        'title', 
        'project_area', 
        'project_keyword', 
        'project_type', 
        'other_type',
        'prerequisite',
        'MSc?',
        'description',
    ]  # Add your field names here

    writer.writerow(fields)

    # Iterate over the queryset
    for obj in queryset:
        row = [
            obj.id,
            obj.staff.username,
            obj.staff.surname,
            obj.staff.email,
            obj.project_area,
            obj.title,
            obj.project_area,
            ', '.join(str(value) for value in obj.project_keyword.all()),
            obj.project_type,
            ', '.join(str(value) for value in obj.other_type.all()),
            obj.prerequisite,
            obj.advanced_bio_msc,
            obj.description,
        ]

        writer.writerow(row)

    return response

export_project_as_csv.short_description = "Export selected as CSV"

def export_student_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')

    # Create a timestamped filename
    filename = "%s-%s.csv" % (
        modeladmin.model._meta.verbose_name_plural,
        datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'

    writer = csv.writer(response)

    # Define fields manually
    fields = [
        'id', 
        'student_id',
        'last_name',
        'first_name',
        'email', 
        'masters_pathway?', 
        'prioritised_keywords', 
        'prioritised_types', 
    ]  # Add your field names here

    writer.writerow(fields)

    # Iterate over the queryset
    for obj in queryset:
        row = [
            obj.id,
            obj.student_id,
            obj.last_name,
            obj.first_name,
            obj.email,
            obj.masters_pathway,
            ', '.join(str(value) for value in [
                obj.project_keyword_1,
                obj.project_keyword_2,
                obj.project_keyword_3,
                obj.project_keyword_4,
                obj.project_keyword_5,
            ]),
            ', '.join(str(value) for value in [
                obj.project_type_1,
                obj.project_type_2,
                obj.project_type_3,
                obj.project_type_4,
                obj.project_type_5,
            ]),

        ]

        writer.writerow(row)

    return response

export_student_as_csv.short_description = "Export selected as CSV"
