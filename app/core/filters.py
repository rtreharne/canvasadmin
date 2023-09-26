from django.contrib import admin
from datetime import datetime, timedelta
from .models import Date

def find_term_start_date(year):
    d = datetime(year, 1, 7)
    offset = -d.weekday() #weekday = 0 means monday
    start_year =  d + timedelta(offset)
    today = datetime.today()
    term_start = start_year + timedelta(days=38*7)
    if term_start > today:
        term_start = start_year - timedelta(days=(14*7))

    return term_start

class AssignmentDateFilter(admin.SimpleListFilter):
    title = 'Deadline Filter'
    parameter_name = 'due_at'

    def lookups(self, request, model_admin):
        try:
            filter_tuple = ((x, x) for x in Date.objects.all().order_by('label'))
            return filter_tuple
        except:
            return ()


    def queryset(self, request, queryset):
        
        value = self.value()

        if value != None:
            date_obj = Date.objects.get(label=value)

            if date_obj.start and date_obj.finish:

                return queryset.filter(due_at__gte=date_obj.start, due_at__lte=date_obj.finish)
            
            else:
                return queryset.filter(due_at__isnull=True)

        return queryset
    
    
class SubmissionDateFilter(admin.SimpleListFilter):
    title = 'Deadline Filter'
    parameter_name = 'due_at'

    def lookups(self, request, model_admin):
        try:
            filter_tuple = ((x, x) for x in Date.objects.all().order_by('label'))
            return filter_tuple
        except:
            return ()

    def queryset(self, request, queryset):
        
        value = self.value()

        if value != None:
            date_obj = Date.objects.get(label=value)

            return queryset.filter(assignment__due_at__gte=date_obj.start, assignment__due_at__lte=date_obj.finish)

        return queryset
    
class PreviousDateFilter(admin.SimpleListFilter):
    title = 'Previous Deadline Filter'
    parameter_name = 'previous_term_assignment__due_at'

    def lookups(self, request, model_admin):
        try:
            filter_tuple = ((x, x) for x in Date.objects.all().order_by('label'))
            return filter_tuple
        except:
            return ()

    def queryset(self, request, queryset):
        
        value = self.value()

        print("value: ", value)

        if value != None:
            date_obj = Date.objects.get(label=value)

            return queryset.filter(previous_term_assignment__due_at__gte=date_obj.start, previous_term_assignment__due_at__lte=date_obj.finish)

        return queryset
        



