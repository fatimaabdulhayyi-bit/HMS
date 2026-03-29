from django.contrib import admin
from .models import UserAccount,Patients,Departments, Doctors, PatientFeedback, InPatient, Appointment, DoctorSchedule

admin.site.register(UserAccount)
admin.site.register(Patients)
admin.site.register(Departments)
admin.site.register(Doctors)
admin.site.register(InPatient)
admin.site.register(Appointment)
admin.site.register(DoctorSchedule)

class PatientFeedbackAdmin(admin.ModelAdmin):
    list_display = ( 'patient_name', 'description_short',)
    def patient_name(self, obj):
        return obj.patient.fullname
    patient_name.short_description = 'Patient'
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
admin.site.register(PatientFeedback, PatientFeedbackAdmin)
