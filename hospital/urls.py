from django.urls import path
from . import views


urlpatterns = [
    path("", views.index , name="index"),
    path("signup/", views.signup , name="signup"),
    path('login/', views.login, name='login'),
    path('users/', views.show_users, name='show_users'),
    path('patientreg/', views.patientreg, name='patientreg'), 
    path('doctorreg/', views.doctorreg, name='doctorreg'), 
    path('department/',views.department, name='department'),
    path('add_department/',views.add_department, name='add_department'),
    path('admin_dashboard/',views.admin_dashboard, name='admin_dashboard'),
    path('ambulances/', views.ambulances, name='ambulances'),
    path('manage_appointments/', views.manage_appointments, name='manage_appointments'),
    path('bills/', views.bills, name='bills'),
    path('doctors/', views.doctors, name='doctors'),
    path('emergency/', views.emergency, name='emergency'),
    path('patients/', views.patients, name='patients'),
    path('patient_dashboard/',views.patient_dashboard, name='patient_dashboard'),
    path('appointments/', views.appointments, name='appointments'),
    path('appointment-form/', views.appointment_form, name='appointment_form'),
    path('bill/', views.bill, name='bill'),
    path('feedback/', views.feedback, name='feedback'),
    path('medical-records/', views.medical_records, name='medical_records'),
    path('profile/', views.profile, name='profile'),
    path('doctor_dashboard/',views.doctor_dashboard, name='doctor_dashboard'),
]
