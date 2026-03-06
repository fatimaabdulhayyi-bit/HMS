from django.contrib import admin
from .models import UserAccount,Patients,Departments

admin.site.register(UserAccount)
admin.site.register(Patients)
admin.site.register(Departments)