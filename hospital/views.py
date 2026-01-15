from django.shortcuts import render,redirect
from .models import UserAccount
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login

def signup(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'hospital/forms/sign_up.html', {'error': 'Passwords do not match'})

        if role == "admin" and UserAccount.objects.filter(role="admin").exists():
            return render(request, 'hospital/forms/sign_up.html', {'error': 'Admin already exists.'})

        if fullname and email and password:
            user = UserAccount.objects.create_user(
                email=email,
                fullname=fullname,
                role=role,
                password=password
            )
            
            # If doctor, mark not approved
            if role == 'doctor':
                user.is_approved = False
                user.save()
                return redirect('doctorreg')  # Doctor registration page

            user.save()

            # Redirect based on role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('patientreg')
                
    return render(request, 'hospital/forms/sign_up.html')

def index(request):
    return render(request, 'hospital/index.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.role == 'doctor' and not user.is_approved:
                return render(request, 'hospital/pending_approval.html', 
                              {'error': 'Your account is pending admin approval.'})
            
            auth_login(request, user)  # Login the user
            
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'doctor':
                return redirect('doctor_dashboard')
            else:
                return redirect('patient_dashboard')
        else:
            return render(request, 'hospital/forms/login.html', {'error': 'Invalid credentials.'})

    return render(request, 'hospital/forms/login.html')

def patientreg(request):
    return render(request, 'hospital/forms/patientreg.html')

def doctorreg(request):
    return render(request, 'hospital/forms/doctorreg.html')

def department(request):
    return render(request, 'hospital/admin/department.html')

def add_department(request):
    return render(request, 'hospital/admin/add_department.html')

def admin_dashboard(request):
    return render(request, 'hospital/admin/admin_dashboard.html')

def ambulances(request):
    return render(request, 'hospital/admin/ambulances.html')

def manage_appointments(request):
    return render(request, 'hospital/admin/manage_appointments.html')

def generate_bills(request):
    return render(request, 'hospital/admin/generate_bills.html')

def doctors(request):
    return render(request, 'hospital/admin/doctors.html')

def emergency(request):
    return render(request, 'hospital/admin/emergency.html')

def patients(request):
    return render(request, 'hospital/admin/patients.html')

def doctor_dashboard(request):
    return render(request, 'hospital/doctor/doctor_dashboard.html')

def my_appointments(request):
    return render(request, 'hospital/doctor/my_appointments.html')

def schedules(request):
    return render(request, 'hospital/doctor/schedules.html')

def patient_dashboard(request):
    return render(request, 'hospital/patient/patient_dashboard.html')

def appointments(request):
    return render(request, 'hospital/patient/appointments.html')

def appointment_form(request):
    return render(request, 'hospital/patient/appointment-form.html')

def bill(request):
    return render(request, 'hospital/patient/bill.html')

def feedback(request):
    return render(request, 'hospital/patient/feedback.html')

def medical_records(request):
    return render(request, 'hospital/patient/medical_records.html')

def profile(request):
    return render(request, 'hospital/patient/profile.html')



# ========================= SHOW ALL USERS (DATABASE READ) =========================
def show_users(request):
    users = UserAccount.objects.all()

    html = """
    <html>
    <head><title>All Users</title></head>
    <body>
        <h2>Registered Users</h2>
        <table border="1" cellpadding="8" cellspacing="0">
            <tr>
                <th>ID</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Role</th>
            </tr>
    """

    for user in users:
        html += f"""
            <tr>
                <td>{user.id}</td>
                <td>{user.fullname}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return HttpResponse(html)