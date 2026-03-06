from django.shortcuts import render,redirect,get_object_or_404
from .models import UserAccount, Patients
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages

def signup(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'hospital/forms/sign_up.html', {'error': 'Passwords do not match'})

        if role == "admin":
            # Admin signup form me nahi hai, backend-only
            return render(request, 'hospital/forms/sign_up.html', {'error': 'Admin cannot signup here.'})

        # Check if user exists
        user_exists = UserAccount.objects.filter(email=email).first()
        if user_exists:
            if user_exists.role == 'patient':
                # Patient already exists → redirect to patient registration (profile completion)
                return redirect('login')
            else:
                return render(request, 'hospital/forms/sign_up.html', {'error': 'User with this email already exists.'})

        # Create user
        user = UserAccount.objects.create_user(
            email=email,
            fullname=fullname,
            role=role,
            password=password
        )
        
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        if role == 'doctor':
            user.is_approved = False
            user.save()
            return redirect('doctorreg')

        user.save()
        return redirect('patientreg')  # New patient → go to registration page

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
            
            if user.is_superadmin:
                return redirect('/admin/')

            # 2. Frontend Admin (Normal Admin)
            elif user.role == 'admin' and user.is_admin:
                return redirect('admin_dashboard')
            elif user.role == 'doctor':
                return redirect('doctor_dashboard')
            else:
                return redirect('patient_dashboard')
        else:
            return render(request, 'hospital/forms/login.html', {'error': 'Invalid credentials.'})

    return render(request, 'hospital/forms/login.html')

def patientreg(request):
    if request.method == 'POST':
        # Form se data uthana
        guardian_name = request.POST.get('guardian_name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        cnic = request.POST.get('cnic')
        phone = request.POST.get('phone')
        blood_group = request.POST.get('blood_group')
        address = request.POST.get('address')

        # Database mein save karna
        Patients.objects.create(
            user=request.user, # Ab ye error nahi dega kyunki user login ho chuka hai
            guardian_name=guardian_name,
            dob=dob,
            gender=gender,
            cnic=cnic,
            phone=phone,
            blood_group=blood_group,
            address=address
        )
        return redirect('patient_dashboard')
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

def bill_list(request):
    return render(request, 'hospital/admin/bill_list.html')

def doctors(request):
    return render(request, 'hospital/admin/doctors.html')

def emergency(request):
    return render(request, 'hospital/admin/emergency.html')

def patients(request):
    # Database se saray patients ka data unke user account ke sath mangwana
    # select_related use karne se performance behtar hoti hai
    patients = Patients.objects.all().select_related('user')
    
    context = {
        'patients': patients
    }
    return render(request, 'hospital/admin/patients.html', context)

def add_patient(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname')
        guardian_name = request.POST.get('guardian_name') 
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        patient_type = request.POST.get('patient_type')
        blood_group = request.POST.get('blood_group') # <--- Ab ye value pakrein
        cnic = request.POST.get('cnic')
        address = request.POST.get('address')
        status = request.POST.get('status')

        try:
            # 1. User banayein
            new_user = UserAccount.objects.create_user(
                email=email,
                fullname=fullname,
                role='patient',
                password="Patient@123" 
            )
            
            # 2. Patient Profile banayein
            Patients.objects.create(
                user=new_user,
                guardian_name=guardian_name,
                dob=dob,
                gender=gender,
                phone=phone,
                cnic=cnic,
                address=address,
                patient_type=patient_type,
                blood_group=blood_group, # <--- Model mein save karein
                status=status
            )
            return redirect('patients') 

        except Exception as e:
            return render(request, 'hospital/admin/add_patient.html', {'error': e})
    return render(request, 'hospital/admin/add_patient.html')

def delete_patient(request, pk):
    # 1. Patient ko dhoondna
    patient = get_object_or_404(Patients, id=pk)
    
    try:
        # 2. UserAccount ko delete karna (CASCADE ki wajah se profile khud hi udd jayegi)
        user = patient.user
        user.delete() 
        
        messages.success(request, "Patient and their account deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
        
    return redirect('patients')

def update_patient(request, pk):
    # 1. Pehle patient ka record database se nikalein (ID ke zariye)
    patient = get_object_or_404(Patients, id=pk)
    user = patient.user  # Patient se juda hua user account
    if request.method == "POST":
        # 2. Form se naya data pakrein

        user.fullname = request.POST.get('fullname')
        user.email = request.POST.get('email')
        patient.guardian_name = request.POST.get('guardian_name')
        patient.phone = request.POST.get('phone')
        patient.dob = request.POST.get('dob')
        patient.gender = request.POST.get('gender')
        patient.blood_group = request.POST.get('blood_group')
        patient.patient_type = request.POST.get('patient_type')
        patient.cnic = request.POST.get('cnic')
        patient.address = request.POST.get('address')
        patient.status = request.POST.get('status')
        try:
            # 3. Dono tables ko save karein

            user.save()
            patient.save()
            messages.success(request, "Patient record updated successfully!")
            return redirect('patients')
        except Exception as e:
            messages.error(request, f"Error updating record: {e}")
    # 4. GET request par purana data form mein bharna

    context = {
        'patient': patient,
    }
    return render(request, 'hospital/admin/update_patient.html', context)


def IPD(request):
    return render(request, 'hospital/admin/IPD.html')

def add_IPrecord(request):
    return render(request, 'hospital/admin/add_IP-record.html')

def add_doctor(request):
    return render(request, 'hospital/admin/add_doctor.html')

def add_appointment(request):
    return render(request, 'hospital/admin/add_appointment.html')

def doctor_dashboard(request):
    return render(request, 'hospital/doctor/doctor_dashboard.html')

def my_appointments(request):
    return render(request, 'hospital/doctor/my_appointments.html')

def add_schedule(request):
    return render(request, 'hospital/doctor/add_schedule.html')
def profiledoc(request):
    return render(request, 'hospital/doctor/profiledoc.html')
def view_medical_record(request):
    return render(request, 'hospital/doctor/view_medical_record.html' )
def doctor_schedule(request):
    return render(request, 'hospital/doctor/doctor_schedule.html' )
def add_medical_record(request):
    return render(request, 'hospital/doctor/add_medical_record.html' )

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

def doctor_recommendation(request):
    return render(request, 'hospital/doctor_recommendation.html')

def logout_view(request):
    logout(request)
    return redirect('login') 
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