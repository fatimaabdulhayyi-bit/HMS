from django.shortcuts import render,redirect,get_object_or_404
from .models import UserAccount, Patients, Departments, Doctors, PatientFeedback, InPatient
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
    active_depts = Departments.objects.filter(status=True)
    total_patients = Patients.objects.count()
    total_departments = Departments.objects.count()
    context = {
        'total_patients': total_patients,
        'total_departments': total_departments,
        'departments': active_depts
    }
    return render(request, 'hospital/index.html', context)
   
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

    depts = Departments.objects.filter(status=True)

    if request.method == "POST":

        father_name = request.POST.get('father_name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        cnic = request.POST.get('cnic')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        dept_id = request.POST.get('dept')
        license_number = request.POST.get('license')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')

        department = Departments.objects.get(id=dept_id)

        Doctors.objects.create(
            user=request.user,
            father_name=father_name,
            dob=dob,
            gender=gender,
            cnic=cnic,
            phone=phone,
            address=address,
            department=department,
            license_number=license_number,
            qualification=qualification,
            experience=experience
        )
        logout(request)
        messages.success(request, "Registration submitted successfully. Please wait for admin approval.")

        return redirect('login')

    return render(request, 'hospital/forms/doctorreg.html', {'departments': depts})

def department(request):
     # Database se saray patients ka data unke user account ke sath mangwana
    # select_related use karne se performance behtar hoti hai
    departments = Departments.objects.all()
    
    context = {
        'departments': departments
    }
    return render(request, 'hospital/admin/department.html', context)

def add_department(request):
    if request.method == "POST":
        name = request.POST.get('department_name')
        desc = request.POST.get('description')
        status_val = request.POST.get('status')
        
        # Status ko boolean mein convert karna
        status = True if status_val == "Active" else False
        
        Departments.objects.create(name=name, description=desc, status=status)
        return redirect('department')
    return render(request, 'hospital/admin/add_department.html')

def update_department(request, pk):
    dept = get_object_or_404(Departments, id=pk)
    
    if request.method == "POST":
        dept.name = request.POST.get('department_name')
        dept.description = request.POST.get('description')
        dept.status = True if request.POST.get('status') == "Active" else False
        dept.save()
        messages.success(request, "Department updated!")
        return redirect('department')
        
    return render(request, 'hospital/admin/update_department.html', {'dept': dept})

def delete_department(request, pk):
    dept = get_object_or_404(Departments, id=pk)
    dept.delete()
    messages.success(request, "Department deleted!")
    return redirect('department')

def admin_dashboard(request):
    total_patients = Patients.objects.count()
    total_departments = Departments.objects.count()
    pending_doctors = Doctors.objects.filter(is_approved=False)
    total_doctors = Doctors.objects.count()
    
    active_InPatients_count = InPatient.objects.filter(is_discharged=False).count()
    
    context = {
        'total_patients': total_patients,
        'total_doctors' : total_doctors,
        'total_departments': total_departments,
        'pending_doctors': pending_doctors,
        'total_InPatients': active_InPatients_count 
    }
    return render(request, 'hospital/admin/admin_dashboard.html', context)

def approve_doctor(request, doctor_id):

    doctor = get_object_or_404(Doctors, id=doctor_id)

    doctor.is_approved = True
    doctor.save()
    
    user = doctor.user
    user.is_approved = True
    user.save()

    return redirect('admin_dashboard')

def reject_doctor(request, doctor_id):

    doctor = get_object_or_404(Doctors, id=doctor_id)
    user = doctor.user

    doctor.delete()
    user.delete()    # Delete user account
    return redirect('admin_dashboard')

def manage_appointments(request):
    return render(request, 'hospital/admin/manage_appointments.html')

def generate_bills(request):
    return render(request, 'hospital/admin/generate_bills.html')

def bill_list(request):
    return render(request, 'hospital/admin/bill_list.html')

def doctors(request):
    all_doctors = Doctors.objects.filter(is_approved=True) 
    return render(request, 'hospital/admin/doctors.html', {'doctors': all_doctors})

def add_doctor(request):
    if request.method == "POST":
        email = request.POST.get('email')
        fullname = request.POST.get('fullname')
        password = "Doctor@123"  # Standard password for new accounts

        try:
            # 1. Check karein ke user pehle se exist toh nahi karta
            if UserAccount.objects.filter(email=email).exists():
                messages.error(request, "This email is already registered.")
                return redirect('add_doctor')

            # 2. UserAccount create karein 
            # (Sirf wahi fields pass karein jo UserAccount model mein hain)
            user = UserAccount.objects.create_user(
                email=email, 
                password=password, 
                fullname=fullname, 
                role='doctor'
            )

            # 3. Department fetch karein
            dept_id = request.POST.get('dept')
            dept_obj = Departments.objects.get(id=dept_id) if dept_id else None

            # 4. Doctors Profile create karein
            # String 'True' ko boolean True mein convert karna zaroori hai
            status_check = request.POST.get('is_approved') == 'True'

            Doctors.objects.create(
                user=user,
                father_name=request.POST.get('father_name'),
                dob=request.POST.get('dob'),
                gender=request.POST.get('gender'),
                cnic=request.POST.get('cnic'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                department=dept_obj,
                license_number=request.POST.get('license_number'),
                qualification=request.POST.get('qualification'),
                experience=request.POST.get('experience'),
                is_approved=status_check
            )
            
            messages.success(request, f"Doctor {fullname} created successfully!")
            return redirect('doctors')
            
        except Exception as e:
            # Agar koi error aaye toh console/terminal mein print hoga
            print(f"Error creating doctor: {e}") 
            messages.error(request, f"Registration failed: {e}")

    depts = Departments.objects.filter(status=True)
    return render(request, 'hospital/admin/add_doctor.html', {'departments': depts})

def update_doctor(request, pk):
    doctor = get_object_or_404(Doctors, id=pk)
    depts = Departments.objects.filter(status=True)

    if request.method == "POST":
        try:
            # Updating Profile Fields
            doctor.father_name = request.POST.get('father_name')
            doctor.dob = request.POST.get('dob')
            doctor.gender = request.POST.get('gender')
            doctor.cnic = request.POST.get('cnic')
            doctor.phone = request.POST.get('phone')
            doctor.address = request.POST.get('address')
            
            # Professional details
            dept_id = request.POST.get('dept')
            if dept_id:
                doctor.department = Departments.objects.get(id=dept_id)
            
            doctor.qualification = request.POST.get('qualification')
            doctor.experience = request.POST.get('experience')
            doctor.license_number = request.POST.get('license_number')
            
            # Status update
            doctor.is_approved = request.POST.get('is_approved') == 'True'

            doctor.save()
            messages.success(request, f"Dr. {doctor.user.fullname}'s details updated.")
            return redirect('doctors')

        except Exception as e:
            messages.error(request, f"Update failed: {e}")
            return redirect('update_doctor')


    return render(request, 'hospital/admin/update_doctor.html', {
        'doctor': doctor, 
        'departments': depts
    })
def delete_doctor(request, pk):
    doctor = get_object_or_404(Doctors, id=pk)
    
    try:
        # 2. UserAccount ko delete karna (CASCADE ki wajah se profile khud hi udd jayegi)
        user = doctor.user
        user.delete() 
        
        messages.success(request, "Doctor and their account deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
        
    return redirect('doctors')

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

def In_Patient(request):
    # 'ipd_records' variable name use kiya hai jo template mein loop ho raha hai
    records = InPatient.objects.all().order_by('-admission_date')
    return render(request, 'hospital/admin/In_patient.html', {'ipd_records': records})

# 2. Add IPD Record
def add_IPrecord(request):
    if request.method == "POST":
        p_id = request.POST.get('patient')
        d_id = request.POST.get('doctor')
        r_no = request.POST.get('room_no')
        b_no = request.POST.get('bed_no')

        if InPatient.objects.filter(room_no=r_no, bed_no=b_no, is_discharged=False).exists():
            messages.error(request, f"Room {r_no}, Bed {b_no} is already occupied!")
        else:
            InPatient.objects.create(
                patient_id=p_id,
                doctor_id=d_id,
                room_no=r_no,
                bed_no=b_no,
                admission_date=request.POST.get('admission_date'),
                admission_time=request.POST.get('admission_time'),
                diagnosis=request.POST.get('diagnosis'),
                is_discharged=(request.POST.get('status') == 'Discharged')
            )
            messages.success(request, "IPD Record added successfully!")
            return redirect('In_Patient') 

    context = {
        'patients': Patients.objects.all(),
        'doctors': Doctors.objects.all()
    }
    return render(request, 'hospital/admin/add_IP-record.html', context)

# 3. Update IPD Record
def update_In_Patient(request, pk):
    record = get_object_or_404(InPatient, pk=pk)
    
    if request.method == "POST":
        r_no = request.POST.get('room_no')
        b_no = request.POST.get('bed_no')

        occupied = InPatient.objects.filter(room_no=r_no, bed_no=b_no, is_discharged=False).exclude(pk=pk).exists()

        if occupied:
            messages.error(request, f"Bed {b_no} is already occupied by someone else!")
        else:
            record.patient_id = request.POST.get('patient')
            record.doctor_id = request.POST.get('doctor')
            record.room_no = r_no
            record.bed_no = b_no
            record.admission_date = request.POST.get('admission_date')
            record.admission_time = request.POST.get('admission_time')
            record.diagnosis = request.POST.get('diagnosis')
            record.is_discharged = (request.POST.get('status') == 'Discharged')
            record.save()
            
            messages.success(request, "Record updated successfully!")
            return redirect('In_Patient')

    context = {
        'record': record,
        'patients': Patients.objects.all(),
        'doctors': Doctors.objects.all(),
    }
    return render(request, 'hospital/admin/update_In_Patient.html', context)

# 4. Discharge Patient
def discharge_patient(request, pk):
    record = get_object_or_404(InPatient, pk=pk)
    record.is_discharged = True
    record.save()
    messages.success(request, f"{record.patient.user.fullname} has been discharged.")
    return redirect('In_Patient')

def add_appointment(request):
    return render(request, 'hospital/admin/add_appointment.html')

def doctor_dashboard(request):
    return render(request, 'hospital/doctor/doctor_dashboard.html')

def my_appointments(request):
    return render(request, 'hospital/doctor/my_appointments.html')

def add_schedule(request):
    return render(request, 'hospital/doctor/add_schedule.html')

def profiledoc(request):

    doctor = Doctors.objects.filter(user=request.user).select_related('user').first()

    context = {
        'doctor': doctor
    }

    return render(request, 'hospital/doctor/profiledoc.html', context)

def edit_docprofile(request):
    doctor = get_object_or_404(Doctors, user=request.user)
    all_departments = Departments.objects.all()

    if request.method == "POST":
        doctor.father_name = request.POST.get('father_name')
        doctor.dob = request.POST.get('dob')
        doctor.gender = request.POST.get('gender')
        doctor.cnic = request.POST.get('cnic')
        doctor.phone = request.POST.get('phone')
        doctor.address = request.POST.get('address')
        
        dept_id = request.POST.get('dept')
        if dept_id:
            doctor.department = Departments.objects.get(id=dept_id)
            
        doctor.qualification = request.POST.get('qualification')
        doctor.experience = request.POST.get('experience')
        doctor.license_number = request.POST.get('license_number')
        
        doctor.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profiledoc')

    context = {
        'doctor': doctor,
        'departments': all_departments
    }
    return render(request, 'hospital/doctor/edit_docprofile.html', context)

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
    if request.method == "POST":
        description = request.POST.get('description')
        
        try:
            # Feedback ko save karna
            PatientFeedback.objects.create(
                patient=request.user, # Logged-in patient
                description=description
            )
            
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")
    return render(request, 'hospital/patient/feedback.html')

def medical_records(request):
    return render(request, 'hospital/patient/medical_records.html')

def profile(request):
    patient = Patients.objects.filter(user=request.user).select_related('user').first()
    context = {
        'patient': patient
    }
    return render(request, 'hospital/patient/profile.html', context)

def edit_profile(request):
    # Logged-in patient ka data nikalna
    patient = get_object_or_404(Patients, user=request.user)

    if request.method == "POST":
        # Data update logic
        patient.guardian_name = request.POST.get('guardian_name')
        patient.dob = request.POST.get('dob')
        patient.gender = request.POST.get('gender')
        patient.cnic = request.POST.get('cnic')
        patient.phone = request.POST.get('phone')
        patient.address = request.POST.get('address')
        patient.blood_group = request.POST.get('blood_group')
        
        patient.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile') # Wapas main profile par bhej dega

    return render(request, 'hospital/patient/edit_profile.html', {'patient': patient})

def doctor_recommendation(request):
    return render(request, 'hospital/doctor_recommendation.html')

def logout_view(request):
    logout(request)
    return redirect('login') 

