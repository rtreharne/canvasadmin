from django.forms import ModelForm, TextInput, ValidationError, Form, CharField, Textarea, BooleanField, ChoiceField, Select, HiddenInput
from .models import Staff, Project, ProjectKeyword, ProjectType, Module, Student, ProjectArea
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from accounts.models import Department

COVID = (
        (False, 'No'),
        (True, 'Yes')

    )

class ExistingStaffForm(Form):
    username = CharField(max_length=20, required=True)

    def clean_username(self):
        data = self.cleaned_data['username']
        try:
            Staff.objects.get(username=data)
        except:
            raise ValidationError("Username not recognised.")

        return data


class StaffForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)

    agree = BooleanField(label="I have read and agree to the <a href='projects/tandc'>Terms and Conditions</a> "
                               "and <a href='/projects/privacy'>Privacy Policy<a>",
                         required=True)


    class Meta:
        model = Staff
        #fields = '__all__'
        exclude = ('institute_school', 'department', 'other_department', 'number_of_projects',)

    def clean_email(self):
        EMAIL_PERMISSION = ['@liv', '@lstmed']
        email = self.cleaned_data['email']
        print('checking email')
        print(email)
        if not any(s in email for s in EMAIL_PERMISSION):
            raise ValidationError("Please use an @liverpool.ac.uk, @liv.ac.uk  or @lstmed.ac.uk address")
        return email

class ProjectForm(ModelForm):
    ROOMS = (
        ('GF - Gait Lab', 'GROUND FLOOR: Gait Lab'),
        ('GF - Imaging G33', 'GROUND FLOOR: Imaging G33'),
        ('GF - Dissection G35-6', 'GROUND FLOOR: Dissection G35-6'),
        ('GF - micro-CT G38', 'GROUND FLOOR: micro-CT G38'),
        ('FF - Primary', 'FIRST FLOOR: Primary'),
        ('FF - TC 109', 'FIRST FLOOR: TC 109'),
        ('FF - Molecular Biology 110', 'FIRST FLOOR: Molecular Biology 109'),
        ('SF - Primary', 'SECOND FLOOR: Primary'),
        ('SF - Histology 209', 'SECOND FLOOR: Histology 209'),
        ('SF - Imaging 211', 'SECOND FLOOR: Imaging 211'),
        ('SF - 1 deg animal TC 215', 'SECOND FLOOR: 1 deg animal TC 215'),
        ('Other', 'Other'),
    )

    def __init__(self, *args, **kwargs):

        staff = kwargs.pop('staff')
        super(ProjectForm, self).__init__(*args, **kwargs)
        
        # print out initial form values
        print("setting the form up")   
     
        self.fields['project_area'].queryset = ProjectArea.objects.filter(school=staff.school).order_by('title')
        self.fields['project_keyword'].queryset = ProjectKeyword.objects.filter(verified=True, school=staff.school).order_by('title')
        self.fields['project_type'].queryset = ProjectType.objects.filter(school=staff.school).order_by('title')
        self.fields['other_type'].queryset = ProjectType.objects.filter(school=staff.school).order_by('title')
        self.fields['prerequisite'].queryset = Module.objects.filter(school=staff.school).order_by('code')
        self.fields['active'].widget = HiddenInput()
        self.fields['school'].queryset = Department.objects.filter(name=staff.school.name)
        self.fields['school'].initial = staff.school
        self.fields['school'].widget = HiddenInput()
        self.fields['advanced_bio_msc'].required = False

        if staff.school.name == "School of Veterinary Science":
            self.fields['title'] = CharField(widget=HiddenInput(), initial=staff.username, required=False)
            self.fields['description'] = CharField(widget=HiddenInput(), initial=staff.username, required=False)
            self.fields['number'] = CharField(widget=HiddenInput(), initial=1)

        modules = Module.objects.filter(school=staff.school).order_by('code')
        if not modules:
            self.fields['prerequisite'].widget = HiddenInput()
            self.fields['prerequisite'].required = False




    description = CharField(widget=Textarea, help_text="A couple of sentences describing the project area, rather than a specific project.  If you wish to offer projects in two or more distinct research areas that cannot be encompassed by the same description, then you will need to complete a separate version of this form for each (you will be prompted). (Max. 1000 chars.)")
    #other_comments = CharField(widget=Textarea, required=False, label="Optionally, please elaborate.")
    #feedback_text = CharField(label="Additional feedback", widget=Textarea, required=False, help_text='Any additional feedback that can help make this web application better is greatly appreciated. (Max. 200 chars.)')
    #summer_fieldwork = ChoiceField(label="Please indicate if there are reasons (Covid-19 shielding, for example) \
                                          # why you might find it difficult to have face-to-face meetings with project \
                                           #students.",
                                  # choices=COVID,
                                  # required=True,)

    #feedback_consent = BooleanField(label="Are you happy for your feedback to be anonymised and used"
                                          #" in educational research studies?", required=False)

    # iacd fields
    iacd_area = ChoiceField(choices=ROOMS, label="What Lab area in IACD is required?*", help_text="No projects are permitted in the primary tissue culture area", required=False)
    iacd_area_other = CharField(label="If 'Other', where will the project take place?", required=False)
    iacd_training = CharField(widget=Textarea, label="Training*", required=False, help_text="Please describe the training needs of the student, to be provided by the institute.")
    iacd_techniques = CharField(widget=Textarea, label="What techniques will the student use/learn?*", required=False, help_text="Please include the names of persons who will supervise/teach each technique")
    iacd_supervisor_2 = CharField(label="Who will provide supervision if the primary supervisor is unavailable?*", required=False)


    class Meta:
        model = Project
        ordering=('project_keyword')
        exclude = ('other_comments', "feedback", 'feedback_text', "feedback_rating", 'allocate_to_masters', 'confirmed', 'feedback_consent',
                   "bioinfo_msc",
                   "biotech_msc",
                   "i_and_i_msc",
                   "cancer_msc",
                   "sustainable_food_msc",
                   "mbiolsci"
                   )
        

    def clean_project_keyword(self):
        project_keyword = self.cleaned_data['project_keyword']
        if len(project_keyword) < 3:
            raise ValidationError("Please select at least three keywords.")
        if len(project_keyword) > 5:
            raise ValidationError("Please select five keywords or less.")
        return project_keyword
    """
        def clean_prerequisite(self):
        prerequisite = self.cleaned_data['prerequisite']
        if len(prerequisite) > 2:
            raise ValidationError("Please select a maximum of two module prerequisites.")
        return prerequisite
    """


class StudentForm(ModelForm):

    

    def __init__(self, *args, **kwargs):

        school = kwargs.pop('school')
        self.school = school

        super(StudentForm, self).__init__(*args, **kwargs)
        self.fields['area'].queryset = ProjectArea.objects.filter(school=school).order_by('title')
        self.fields['project_type_1'].queryset = ProjectType.objects.filter(school=school).order_by('title')
        self.fields['project_type_2'].queryset = ProjectType.objects.filter(school=school).order_by('title')
        self.fields['project_type_3'].queryset = ProjectType.objects.filter(school=school).order_by('title')
        self.fields['project_type_4'].queryset = ProjectType.objects.filter(school=school).order_by('title')
        self.fields['project_type_5'].queryset = ProjectType.objects.filter(school=school).order_by('title')
        self.fields['project_keyword_1'].queryset = ProjectKeyword.objects.filter(school=school).order_by('title')
        self.fields['project_keyword_2'].queryset = ProjectKeyword.objects.filter(school=school).order_by('title')
        self.fields['project_keyword_3'].queryset = ProjectKeyword.objects.filter(school=school).order_by('title')
        self.fields['project_keyword_4'].queryset = ProjectKeyword.objects.filter(school=school).order_by('title')
        self.fields['project_keyword_5'].queryset = ProjectKeyword.objects.filter(school=school).order_by('title')
        self.fields['modules'].queryset = Module.objects.filter(school=school).order_by('code')

        if school.name != "School of Life Sciences":
            self.fields["masters_pathway"].widget = HiddenInput()
            self.fields['programme'].widget = HiddenInput()
            self.fields['modules'].widget = HiddenInput()
            self.fields['modules'].required = False



    email = CharField(label="Email", help_text="Please use your @liverpool.ac.uk or @student.liverpool.ac.uk address if you have one.")


    student_id = CharField(label="Student ID", required=True, help_text="e.g. 200123456")
    feedback_text = CharField(label="Additional feedback", widget=Textarea, required=False, help_text='Any additional feedback that can help make this web application better is greatly appreciated. (Max. 200 chars.)')
    feedback_consent = BooleanField(label="Are you happy for your feedback to be anonymised and used"
                                          " in educational research studies?", required=False)

    agree = BooleanField(label="I have read and agree to the <a href='/projects/tandc'>Terms and Conditions</a> "
                               "and <a href='/projects/privacy'>Privacy Policy<a>",
                         required=True)

    summer_fieldwork = BooleanField(label="Do you have a disability support plan we should consider in relation to working in groups?",
                         required=False)

    TRUE_FALSE_CHOICES = (
        (True, 'Yes'),
        (False, 'No')
    )

    PROGRAMME_CHOICES = (("Not Applicable", "Not Applicable"),
                       ("Anatomy and Human Biology", "Anatomy and Human Biology"),
                       ("Biochemistry", "Biochemistry"),
                       ("Biological Sciences", "Biological Sciences"),
                       ("Biological and Medical Sciences", "Biological and Medical Sciences"),
                       ("Bioveterinary Sciences", "Bioveterinary Sciences"),
                       ("Genetics", "Genetics"),
                       ("Human Physiology", "Human Physiology"),
                       ("MBiolSci", "MBiolSci"),
                       ("Microbiology", "Microbiology"),
                       ("Pharmacology", "Pharmacology"),
                       ("Tropical Disease Biology", "Tropical Disease Biology"),
                       ("Zoology", "Zoology")
                       )

    programme = ChoiceField(widget=Select(), required=False, initial="1", choices=PROGRAMME_CHOICES,
                                  label="Programme",
                                  help_text="If you're a UG student then select your current programme.")


    #masters = ChoiceField(label="Are you a Masters student",
                           #choices=TRUE_FALSE_CHOICES,
                           #initial=False, widget=Select(), required=True)

    MASTERS_CHOICES = (("1", "Not Applicable"),
                       ("2", "MBiolSci"),
                       ("3", "Advanced Biological Sciences"),
                       ("4", "Bioinformatics"),
                       ("5", "Biotechnology"),
                       ("6", "Infection and Immunity"),
                       ("7", "Cancer Biology and Therapy"),
                       ("8", "Sustainable Food Systems")
                       )

    masters_pathway = ChoiceField(widget=Select(), required=True, initial="1", choices=MASTERS_CHOICES, label="Masters Pathway", help_text="If you're not a Masters student then ignore this.")



    class Meta:
        model = Student
        exclude = ("masters", "feedback_consent", "comments",
                   )

"""
    def clean_email(self):
        EMAIL_PERMISSION = ['@liv', '@lstmed', "@student.liverpool", "@liverpool"]
        email = self.cleaned_data['email']
        print('checking email')
        print(email)
        if not any(s in email for s in EMAIL_PERMISSION):
            raise ValidationError("Please use an @liverpool.ac.uk, @liv.ac.uk, @student.liverpool.ac.uk or @lstmed.ac.uk address")
        return email

"""
"""
    def clean_other_type(self):
        other_type = self.cleaned_data['other_type']
        if len(other_type) > 2:
            raise ValidationError("Please select two secondary types or less.")
        return other_type
"""
