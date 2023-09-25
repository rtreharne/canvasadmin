from django.db import models
from accounts.models import Department

class Sample(models.Model):
    attachment = models.FileField()

class Course(models.Model):
    course_code = models.CharField(max_length=128, unique=True)
    course_id = models.IntegerField(null=True, blank=True)
    course_name = models.CharField(max_length=128)
    course_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT)
    resit_course = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)
        
    def __str__(self):
        return self.course_code
    
class Assignment(models.Model):
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT)
    assignment_name = models.CharField(max_length=500, verbose_name="Assignment")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    points_possible = models.FloatField(null=True, blank=True)
    assignment_id = models.IntegerField(unique=True)
    unlock_at = models.DateTimeField(null=True, blank=True)
    lock_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True, verbose_name="Deadline")
    url = models.URLField()
    needs_grading_count = models.IntegerField(null=True, blank=True)
    published = models.BooleanField(null=True, blank=True, verbose_name="Published")
    anonymous_grading = models.BooleanField(verbose_name="Anonymous Grading")
    active = models.BooleanField(default=True, verbose_name="Active Flag")
    graded = models.IntegerField(null=True, blank=True, default=0)
    ungraded = models.IntegerField(null=True, blank=True, default=0)
    pc_graded = models.FloatField(null=True, blank=True, verbose_name="Graded (%)", default=0)
    not_submitted = models.IntegerField(null=True, blank=True,default=0)
    quiz = models.BooleanField(default=False, verbose_name="Quiz")
    sas_exam = models.BooleanField(default=False, verbose_name="SAS Exam")
    average_score = models.FloatField(null=True, blank=True, verbose_name="Average Score (%)")
    type = models.CharField(max_length=128, null=True, blank=True)
    has_overrides = models.BooleanField(default=False, verbose_name="Overrides")
    posted_at = models.DateTimeField(null=True, blank=True)
    rollover_to_course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.PROTECT, related_name="rollover_to_course")
    previous_term_assignment = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.assignment_name

class Programme(models.Model):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.name

class Student(models.Model):
    sortable_name = models.CharField(max_length=128, verbose_name="Student Name")
    programme = models.ForeignKey(Programme, null=True, blank=True, on_delete=models.CASCADE)
    sis_user_id = models.CharField(max_length=256, null=True, blank=True)
    canvas_id = models.IntegerField(unique=True)
    login_id = models.EmailField(null=True, blank=True)
    
    def __str__(self):
        return self.sortable_name
    
class Submission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    sis_user_id = models.CharField(max_length=128, null=True, blank=True)
    submission_id = models.IntegerField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.CharField(max_length=286, null=True, blank=True)
    seconds_late = models.IntegerField(default=0)
    comments = models.TextField(null=True, blank=True)
    rubric = models.TextField(null=True, blank=True)
    similarity_score = models.FloatField(null=True, blank=True)
    turnitin_url = models.URLField(null=True, blank=True)
    integrity_concern = models.CharField(max_length=128, null=True, blank=True, default=None, verbose_name="Integrity Flag")
    html_url = models.URLField(null=True, blank=True)
    marker = models.CharField(max_length=256, null=True, blank=True)
    marker_email = models.EmailField(null=True, blank=True)
    
    def __str__(self):
        return self.student.sortable_name

class Staff(models.Model):
    name = models.CharField(max_length=128)
    canvas_id = models.IntegerField(null=True, blank=True, unique=True)
    items_graded = models.IntegerField(null=True, blank=True)
    courses_graded_in = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Staff"

    def __str__(self):
        return self.name
    
class Date(models.Model):
    label = models.CharField(max_length=128)
    start = models.DateField(null=True, blank=True)
    finish = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.label








    
