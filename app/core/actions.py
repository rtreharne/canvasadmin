import csv
from django.http import HttpResponse
import datetime

def export_submission_as_csv(modeladmin, request, queryset):
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
        'student',
        'sis_user_id',
        'submission_id',
        'submitted_at',
        'assignment',
        'course',
        'score',
        'posted_at',
        'graded_by',
        'seconds_late',
        'comments',
        'rubric',
        'similarity_score',
        'turnitin_url',
        'integrity_concern',
        'html_url',
        'marker',
        'marker_email',
        'assignment_type',
        
    ]  # Add your field names here

    writer.writerow(fields)

    # Iterate over the queryset
    for obj in queryset:
        row = [
            obj.id,
            obj.student,
            obj.sis_user_id,
            obj.submission_id,
            obj.submitted_at,
            obj.assignment,
            obj.course,
            obj.score,
            obj.posted_at,
            obj.graded_by,
            obj.seconds_late,
            obj.comments,
            obj.rubric,
            obj.similarity_score,
            obj.turnitin_url,
            obj.integrity_concern,
            obj.html_url,
            obj.marker,
            obj.marker_email,
            obj.assignment.assignment_type,
        ]

        writer.writerow(row)

    return response

export_submission_as_csv.short_description = "Export selected as CSV"

