from django.db import models

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
import datetime
from accounts.models import Department

RATING = (
        ('1', '1: Poor'),
        ('2', '2: Bad'),
        ('3', "3: Indifferent"),
        ('4', "4: Good"),
        ('5', "5: Excellent"),
    )

class ProjectArea(models.Model):
    title = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=200, blank=True, default=None, null=True)
    school = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)


    def __str__(self):
        return self.title

class ProjectKeyword(models.Model):
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=200, blank=True, default=None, null=True)
    verified = models.BooleanField(default=True)
    school = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)

    # Add unique constraint for title and school
    class Meta:
        unique_together = ('title', 'school')
        
    def __str__(self):
        return self.title

class ProjectType(models.Model):
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=200, blank=True, default=None, null=True)
    school = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        unique_together = ('title', 'school')

    def __str__(self):
        return self.title

class Staff(models.Model):
    TITLE_CHOICES = (
        ('Dr', 'Dr'),
        ('Prof.', 'Prof.'),
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Miss', 'Miss'),
        ('Ms', 'Ms')
    )
    INSTITUTE = (
        ('1', 'Ageing and Chronic Disease'),
        ('2', 'Human Anatomy Resource Centre'),
        ('3', 'Infection and Global Health'),
        ('4', 'Integrative Biology'),
        ('5', 'Liverpool School of Tropical Medicine'),
        ('6', 'School of Life Sciences'),
        ('7', 'Translational Medicine'),
        ('8', 'Other'),
    )
    DEPARTMENT = (
        ('1', 'Eye and Vision Science'),
        ('2', 'Musculoskeletal Biology I'),
        ('3', 'Musculoskeletal Biology II'),
        ('4', 'Clinical Infection, Microbiology and Immunology'),
        ('5', 'Epidemiology and Population Health'),
        ('6', 'Infection Biology'),
        ('7', 'Biochemistry'),
        ('8', 'Evolution, Ecology and Behaviour'),
        ('9', 'Funtional and Comparative Genomics'),
        ('10', 'Clinical Sciences'),
        ('11', 'International Public Health'),
        ('12', 'Parasitology'),
        ('13', 'Vector Biology'),
        ('14', 'Biostatistics'),
        ('15', 'Cellular and Molecular Physiology'),
        ('16', 'Molecular and Clinical Cancer Medicine'),
        ('17', 'Molecular Pharmacology'),
        ('18', "Women's and Children's Health"),
        ('19', "Not applicable (SOLS, HARC etc)"),
        ('20', "Other"),
    )
    LOCATION = (
        ('Main Campus', 'Main Campus'),
        ('LSTM', 'LSTM'),
        ('Leahurst', 'Leahurst'),
        ('Other', 'Other')
    )
    email = models.EmailField()
    surname = models.CharField(max_length=128)
    initials = models.CharField(max_length=4, help_text="e.g. 'RE for Robert Treharne. We need this to systematically name groups in Canvas")
    title = models.CharField(max_length=5, choices=TITLE_CHOICES)
    username = models.CharField(max_length=10, unique=True, help_text="Standard university login name (MWS, Canvas) - required for setting up Canvas groups etc")
    preferred_forename = models.CharField(max_length=25, blank=True, null=True, default=None)
    institute_school = models.CharField(verbose_name="Institute/School", max_length=128, choices=INSTITUTE, blank=True, default=None, null=True)
    department = models.CharField(max_length=128, blank=True, default=None, null=True)
    other_department = models.CharField(verbose_name="Other", help_text="If your department is not listed then please enter it here.", max_length=28, blank=True, default=None, null=True)
    location = models.CharField(max_length=128, choices=LOCATION)
    other_location = models.CharField(verbose_name="Other", help_text="If your location is not listed then please enter it here.", max_length=28, blank=True, default=None, null=True)
    agree = models.BooleanField(default=False)

    number_of_projects=models.IntegerField(default=3, validators=[MaxValueValidator(10)])
    school = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)



    class Meta:
        verbose_name_plural = 'Staff'

    def __str__(self):
        return self.surname

class Module(models.Model):
    code = models.CharField(max_length=7, unique=True)
    name = models.CharField(max_length=128)
    school = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)


    def __str__(self):
        return "{0}: {1}".format(self.code, self.name)


class Project(models.Model):

    title = models.CharField(max_length=128, help_text="Generic title of project area - not a specific project. (Max. 128 chars.).")
    mbiolsci = models.BooleanField(verbose_name="Suitable for MBiolSci? (runs from October to May)", default=True)
    advanced_bio_msc = models.BooleanField(verbose_name="Suitable for MSc? (12 months duration, from October)", default=False)

    timestamp = models.DateField(auto_now_add=True)
    description = models.CharField(verbose_name='Description of project area', max_length=12800, help_text="A couple of sentences describing the project area, rather than a specific project.  If you wish to offer projects in two or more distinct research areas that cannot be encompassed by the same description, then you will need to complete a separate version of this form for each (you will be prompted). (Max. 1000 chars.).")
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT)
    project_area = models.ForeignKey(ProjectArea, verbose_name='Project cognate area',on_delete=models.PROTECT, related_name="project_area_primary", help_text="Single choice of the most appropriate description of the cognate area of your project(s).")
    project_keyword = models.ManyToManyField(ProjectKeyword, verbose_name="Project keywords", help_text='Hold down "Control", or "Command" on Mac, to select more than one. \
                                                                                                         Please select a minimum of three and a maximum of 5 additional keywords. \
                                                                                                         Do not repeat the one from the previous question. If you feel there is a very obvious keyword missing, then please contact Andy Bates (<a href="mailto:bates@liv.ac.uk">bates@liv.ac.uk</a>).'
                                             )
    suggested_keyword = models.CharField(max_length=128, help_text="If nothing in the list above is suitable, or there has been an obvious omission, please submit additional relevant keywords. Separate each keyword with a comma, e.g. 'keyword1, keyword2'", null=True, default=None, blank=True)
    project_type = models.ForeignKey(ProjectType, verbose_name="Primary project type", on_delete=models.PROTECT)
    other_type = models.ManyToManyField(ProjectType, related_name="other_type", verbose_name="Secondary project types (optional)", null=True, blank=True, default=None, help_text="You can select up to two secondary project types (e.g. Projects with a 'Laboratory' primary type may also involve 'Modelling' etc.)")
    prerequisite = models.ForeignKey(Module, on_delete=models.PROTECT, verbose_name="Prerequisite module",
                                     blank=True,
                                     default=None,
                                     null=True,
                                     help_text="Optionally, please select a single Year 2 pre-requisite module")
    bioinfo_msc = models.BooleanField(verbose_name="Suitable for Bioinformatics MSc? (12 months duration, from October)", default=False)
    biotech_msc = models.BooleanField(verbose_name="Suitable for Biotechnology MSc? (12 months duration, from October)", default=False)
    i_and_i_msc = models.BooleanField(verbose_name="Suitable for Infection and Immunity MSc? (12 months duration, from October)", default=False)
    cancer_msc = models.BooleanField(verbose_name="Suitable for Cancer Biology and Therapy MSc? (12 months duration, from October)", default=False)
    sustainable_food_msc = models.BooleanField(verbose_name="Suitable for Sustainable Food Systems MSc? (12 months duration, from October)", default=False)

    #summer_fieldwork = models.BooleanField(default=False)
    other_comments = models.CharField(max_length=128, blank=True, default=None, null=True)
    number = models.PositiveIntegerField(verbose_name="Number of students", help_text="I.e. how many students can do this project simultaneously? (normally max 4).", default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    allocate_to_masters = models.PositiveIntegerField(verbose_name="Allocated to Masters", default=0, editable=True)

    # iacd fields
    iacd_area = models.CharField(max_length=128, blank=True, default=None, null=True)
    iacd_area_other = models.CharField(max_length=500, blank=True, default=None, null=True)
    iacd_training = models.CharField(max_length=10000, blank=True, default=None, null=True)
    iacd_techniques = models.CharField(max_length=10000, blank=True, default=None, null=True)
    iacd_supervisor_2 = models.CharField(max_length=500, blank=True, default=None, null=True)

    confirmed = models.BooleanField(default=True)

    feedback_rating = models.CharField(max_length=128, choices=RATING, default='3', verbose_name="How would you rate your experience using this web app?")
    feedback_text = models.CharField(max_length=10000, verbose_name="Additional feedback", blank=True, default=None, null=True, help_text='Any additional feedback that can help make this web application better is greatly appreciated. (Max. 2000 chars.).')
    feedback_consent = models.BooleanField(default=False)

    active = models.BooleanField(default=True)
    school = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)


    def __str__(self):
        return self.staff.surname

class Student(models.Model):

    PRIORITY = (
        ("1", "Project Keywords"),
        ("2", "Project Type"),
        ("3", "It doesn't matter"),
    )
    
    student_id = models.CharField(max_length=128, validators=[RegexValidator(regex='^\d{9}$', message='This must be a nine digit number', code='nomatch')], unique=False)
    last_name = models.CharField(max_length=28)
    first_name = models.CharField(max_length=28)
    email = models.EmailField(max_length=128)
    programme = models.CharField(max_length=128, default="1")
    #masters = models.BooleanField(default=False)


    masters_pathway = models.CharField(verbose_name="Masters Pathway?" ,max_length=10000, default="1")
    modules = models.ManyToManyField(Module, verbose_name="Your Second Year Modules",
                                     blank=True,
                                     default=None,
                                     help_text='If you are an UG student please input all your second year modules. Hold down "Control", or "Command" on Mac, to select more than one.')

    area = models.ForeignKey(ProjectArea, on_delete=models.PROTECT, null=True)



    priority = models.CharField(verbose_name="Allocation Priority", max_length=128, choices=PRIORITY, default="3",
                                help_text="Choose what is more important to you. E.g. If you are more concerned with being"
                                          " allocated a project that satisfies your preferences for project type over keywords"
                                          " select 'Project Type'. Your preferences will be weighted accordingly.")

    project_keyword_1 = models.ForeignKey(ProjectKeyword, on_delete=models.PROTECT, related_name="project_keyword_1")
    project_keyword_2 = models.ForeignKey(ProjectKeyword, on_delete=models.PROTECT, related_name="project_keyword_2")
    project_keyword_3 = models.ForeignKey(ProjectKeyword, on_delete=models.PROTECT, related_name="project_keyword_3")
    project_keyword_4 = models.ForeignKey(ProjectKeyword, on_delete=models.PROTECT, related_name="project_keyword_4")
    project_keyword_5 = models.ForeignKey(ProjectKeyword, on_delete=models.PROTECT, related_name="project_keyword_5")
    project_type_1 = models.ForeignKey(ProjectType, on_delete=models.PROTECT, related_name="project_type_1")
    project_type_2 = models.ForeignKey(ProjectType, on_delete=models.PROTECT, related_name="project_type_2")
    project_type_3 = models.ForeignKey(ProjectType, on_delete=models.PROTECT, related_name="project_type_3")
    project_type_4 = models.ForeignKey(ProjectType, on_delete=models.PROTECT, related_name="project_type_4")
    project_type_5 = models.ForeignKey(ProjectType, on_delete=models.PROTECT, related_name="project_type_5")

    summer_fieldwork = models.BooleanField(verbose_name="Support Plan", default=False)
    comments = models.CharField(max_length=1000, blank=True, default=None, null=True)

    feedback_consent = models.BooleanField(default=True)
    feedback_rating = models.CharField(max_length=20, choices=RATING, default='3', verbose_name="How would you rate your experience using this web app?")
    feedback_text = models.CharField(max_length=200, verbose_name="Additional feedback", blank=True, default=None, null=True, help_text='Any additional feedback that can help make this web application better is greatly appreciated. (Max. 200 chars.).')
    agree = models.BooleanField(default=False)
    timestamp = models.DateField(auto_now=True, null=True, blank=True)
    school = models.ForeignKey(Department, on_delete=models.PROTECT, null=True, blank=True)
    class Meta:
        unique_together = ('student_id', 'programme')


    def __str__(self):
        return self.student_id
    



