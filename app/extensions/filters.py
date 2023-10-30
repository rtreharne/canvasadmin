from django.contrib import admin
from datetime import datetime, timedelta
from .models import Date

class DateFilter(admin.SimpleListFilter):
    title = 'Date Filter'
    parameter_name = 'Date'

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