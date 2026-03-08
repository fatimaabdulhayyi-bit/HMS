from django.contrib import admin
from .models import UserAccount,Patients,Departments, Doctors

admin.site.register(UserAccount)
admin.site.register(Patients)
admin.site.register(Departments)
admin.site.register(Doctors)