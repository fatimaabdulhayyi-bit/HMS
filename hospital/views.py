from django.shortcuts import render,redirect,get_object_or_404
from .models import UserAccount, Patients, Departments, Doctors, PatientFeedback, InPatient, DoctorSchedule, Appointment, Bills, BillItems
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Max
from datetime import date,datetime,timedelta
from django.db import transaction

def signup(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'hospital/forms/sign_up.html',
                          {'error': 'Passwords do not match'})

        # Check if user already exists
        user = UserAccount.objects.filter(email=email).first()
        if user:

            # Check doctor registration
            if user.role == "doctor":
                doctor_exists = Doctors.objects.filter(user=user).exists()

                if not doctor_exists:
                    auth_login(request, user)
                    return redirect('doctorreg')
                else:
                    messages.success(request, "User already exist. Please login")
                    return redirect('login')

            # Check patient registration
            if user.role == "patient":
                patient_exists = Patients.objects.filter(user=user).exists()

                if not patient_exists:
                    auth_login(request, user)
                    return redirect('patientreg')
                else:
                    messages.success(request, "User already exist. Please login")
                    return redirect('login')

            return redirect('login')

        # Create new user
        user = UserAccount.objects.create_user(
            email=email,
            fullname=fullname,
            role=role,
            password=password
        )

        auth_login(request, user)

        if role == "doctor":
            user.is_approved = False
            user.save()
            return redirect('doctorreg')

        return redirect('patientreg')

    return render(request, 'hospital/forms/sign_up.html')

def index(request):
    active_depts = Departments.objects.filter(status=True)
    total_patients = Patients.objects.count()
    total_departments = Departments.objects.count()
    total_doctors = Doctors.objects.filter(is_approved=True).count()
    total_appointments = Appointment.objects.count()

    context = {
        'total_patients': total_patients,
        'total_departments': total_departments,
        'departments': active_depts,
        'total_doctors' : total_doctors,
        'total_appointments': total_appointments,
    }
    return render(request, 'hospital/index.html', context)
   
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)

        if user is not None:
            # 1. Pehle user ko login karwa dein taake session mil jaye
            auth_login(request, user)

            if user.role == 'doctor':
                doctor_exists = Doctors.objects.filter(user=user).exists()
                
                if not doctor_exists:
                    return redirect('doctorreg')
                
                if not user.is_approved:
                    messages.warning(request, "Please wait for admin approval.")
                    return redirect('login')
                
                return redirect('doctor_dashboard')

            elif user.role == 'patient':
                patient_exists = Patients.objects.filter(user=user).exists()
                if not patient_exists:
                    return redirect('patientreg')
                return redirect('patient_dashboard')

            # 3. Admin / Superadmin logic
            elif user.is_superadmin:
                messages.warning(request, "You have no access to this page.")
                return redirect('/login/')
            
            elif user.role == 'admin' and user.is_admin:
                return redirect('admin_dashboard')

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
    total_doctors = Doctors.objects.filter(is_approved=True).count()
    total_appointments = Appointment.objects.count()
    pending_opd = Appointment.objects.filter(status='Completed').exclude(status='Billed') 
    
    pending_ipd = InPatient.objects.filter(
        is_discharged=True
    ).exclude(
        status='Billed'
    )    
    active_InPatients_count = InPatient.objects.filter(is_discharged=False).count()
    ongoing_appointments = Appointment.objects.filter(
        appointment_date=date.today(),
        status__in=['Pending', 'Serving']
    ).order_by('token')[:5] # Top 5 dikhane ke liye
    
    context = {
        'total_patients': total_patients,
        'total_doctors' : total_doctors,
        'total_departments': total_departments,
        'pending_doctors': pending_doctors,
        'total_InPatients': active_InPatients_count,
        'total_appointments': total_appointments,
        'ongoing_appointments': ongoing_appointments,
        'pending_opd_bills': pending_opd,
        'pending_ipd_bills': pending_ipd,
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
    # select_related use karne se doctor aur department ka data aik hi query mein aa jayega
    # -appointment_date ka matlab hai ke latest appointments sab se upar aayengi
    all_appointments = Appointment.objects.all().select_related(
        'doctor__user', 
        'department', 
        'patient_user'
    ).order_by('-appointment_date', 'token')

    context = {
        'appointments': all_appointments
    }
    return render(request, 'hospital/admin/manage_appointments.html', context)

def add_appointment(request):
    if request.method == "POST":
        patient_id = request.POST.get('patient')
        dept_id = request.POST.get('department')
        doc_id = request.POST.get('doctor')
        app_date = request.POST.get('appointment_date')
        app_time = request.POST.get('appointment_time')
        status = request.POST.get('status')

        # 1. Patient ki details fetch karein (Auto-filling for Appointment model)
        patient_obj = get_object_or_404(Patients, id=patient_id)
        
        # Age calculate karein (agar model mein method nahi hai toh manually)
        today = date.today()
        dob = patient_obj.dob
        calculated_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # 2. Token Generation (Aaj ka max token + 1)
        last_token = Appointment.objects.filter(
            doctor_id=doc_id, 
            appointment_date=app_date
        ).aggregate(Max('token'))['token__max'] or 0
        new_token = last_token + 1

        # 3. Create Appointment
        Appointment.objects.create(
            patient_user=patient_obj, # Connect to UserAccount
            fullname=patient_obj.user.fullname,
            age=calculated_age,
            gender=patient_obj.gender,
            contact=patient_obj.phone,
            department_id=dept_id,
            doctor_id=doc_id,
            appointment_date=app_date,
            appointment_time=app_time,
            token=new_token,
            status=status
        )

        messages.success(request, f"Appointment created! Token #{new_token} assigned.")
        return redirect('manage_appointments') # Admin appointments list par wapas

    # GET Request: Dropdowns fill karne k liye
    context = {
        'patients': Patients.objects.all(),
        'departments': Departments.objects.filter(status=True),
        'doctors': Doctors.objects.filter(is_approved=True), # Default list (AJAX isay update kar dega)
    }
    return render(request, 'hospital/admin/add_appointment.html', context)

def view_appointment(request, pk):
    # Specific appointment uthayein ID (pk) ke zariye
    appointment = get_object_or_404(Appointment, id=pk)
    
    # Agar aap mazeed details dikhana chahti hain jo profile mein hain:

    patient_profile = appointment.patient_user
    context = {
        'appt': appointment,
        'patient': patient_profile
    }
    return render(request, 'hospital/admin/view_appointment.html', context)

def delete_appointment(request, pk):

    # Ye function appointment ko cancel karne ke liye use ho raha hai

    appointment = get_object_or_404(Appointment, id=pk)

    

    if appointment.status != 'Completed':

        appointment.status = 'Cancelled'

        appointment.save()

        messages.success(request, "Appointment has been cancelled successfully.")

    else:

        messages.error(request, "Completed appointments cannot be cancelled.")

        

    return redirect('manage_appointments')

def generate_bills(request, p_type=None, id=None):
    selected_patient = None
    initial_type = ""
    source_obj = None
    
    # 1. Fetching Patient based on OPD/IPD
    if p_type and id:
        if p_type == 'OPD':
            appt = get_object_or_404(Appointment, id=id)
            selected_patient = appt.patient_user
            initial_type = "Out-Patient"
            source_obj = appt
        elif p_type == 'IPD':
            ipd = get_object_or_404(InPatient, id=id)
            selected_patient = ipd.patient
            initial_type = "In-Patient"
            source_obj = ipd

    if request.method == "POST":
        try:
            with transaction.atomic():
                user_id = request.POST.get('patient_user_id')
                patient_obj = get_object_or_404(Patients, user_id=user_id)
                p_status = request.POST.get('payment_status')
                
                # 2. Create Main Bill
                bill = Bills.objects.create(
                    patient=patient_obj,
                    patient_type=initial_type, # Using backend variable for safety
                    bill_date=request.POST.get('bill_date') or date.today(),
                    admission_date=request.POST.get('admission_date') if request.POST.get('admission_date') else None,
                    discharge_date=request.POST.get('discharge_date') if request.POST.get('discharge_date') else None,
                    staying_days=int(request.POST.get('staying_days') or 0),
                    payment_status=p_status,
                    payment_method=request.POST.get('payment_method') if p_status == "Paid" else "Unpaid",
                    amount_paid=request.POST.get('amount_paid') if p_status == "Paid" else 0,
                    grand_total=0 
                )

                # 3. Process Dynamic Items
                services = request.POST.getlist('service_name[]')
                qtys = request.POST.getlist('qty[]')
                prices = request.POST.getlist('unit_price[]')
                discounts = request.POST.getlist('discount[]')

                total_sub = 0
                total_disc = 0

                for i in range(len(services)):
                    s_name = services[i].strip()
                    if not s_name: continue

                    q = int(qtys[i] or 1)
                    p = float(prices[i] or 0)
                    d = float(discounts[i] or 0)
                    
                    # BACKEND NEGATIVE CHECK
                    line_total = (q * p) - d
                    if line_total < 0: line_total = 0
                    
                    BillItems.objects.create(
                        bill=bill,
                        service_name=s_name,
                        quantity=q,
                        unit_price=p,
                        discount=d,
                        total=line_total
                    )
                    total_sub += (q * p)
                    total_disc += d

                # 4. Final Totals Update (with safety check)
                bill.subtotal = total_sub
                bill.total_discount = total_disc
                final_grand = total_sub - total_disc
                bill.grand_total = max(0, final_grand)
                bill.save()
                
                # 5. STATUS UPDATE (Dashboard se hatane ke liye)
                if p_type == 'OPD':
                    Appointment.objects.filter(id=id).update(status='Billed') 
                elif p_type == 'IPD':
                    InPatient.objects.filter(id=id).update(status='Billed', is_discharged=True)

                messages.success(request, f"Bill #{bill.id} generated successfully!")
                return redirect('bill_list')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
        'selected_patient': selected_patient,
        'initial_type': initial_type,
        'source_obj': source_obj,
        'today': date.today(),
    }
    return render(request, 'hospital/admin/generate_bills.html', context)

def bill_list(request):
    bills = Bills.objects.all().order_by('-created_at')
    return render(request, 'hospital/admin/bill_list.html', {'bills': bills})

def view_bill(request, pk):
    # 1. Pehle Bill nikalein
    bill = get_object_or_404(Bills, id=pk)
    items = BillItems.objects.filter(bill=bill)
    context = {
        'bill': bill,
        'items': items  
    }
    return render(request, 'hospital/admin/view_bill.html', context)

def edit_bill(request, pk):
    bill = get_object_or_404(Bills, id=pk)
    items = BillItems.objects.filter(bill=bill)
    
    if request.method == "POST":
        with transaction.atomic(): # Taake agar koi error aaye to data kharab na ho
            # 1. Main Bill Fields Update karein
            bill.bill_date = request.POST.get('bill_date')
            bill.payment_status = request.POST.get('payment_status')
            bill.payment_method = request.POST.get('payment_method')
            bill.amount_paid = request.POST.get('amount_paid', 0)
            
            if bill.patient_type == "In-Patient":
                bill.discharge_date = request.POST.get('discharge_date')
                bill.staying_days = request.POST.get('staying_days', 0)

            # 2. Purane Items Delete karein
            BillItems.objects.filter(bill=bill).delete()

            # 3. Naye Items Save karein (Loop)
            services = request.POST.getlist('service_name[]')
            qtys = request.POST.getlist('qty[]')
            prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')

            total_subtotal = 0
            total_discount = 0

            for i in range(len(services)):
                q = int(qtys[i])
                p = float(prices[i])
                d = float(discounts[i])
                line_total = (q * p) - d
                
                BillItems.objects.create(
                    bill=bill,
                    service_name=services[i],
                    quantity=q, # Model field: quantity
                    unit_price=p,
                    discount=d,
                    total=line_total # Model field: total
                )
                
                total_subtotal += (q * p)
                total_discount += d

            # 4. Bill ke totals update karein
            bill.subtotal = total_subtotal
            bill.total_discount = total_discount
            bill.grand_total = total_subtotal - total_discount
            bill.save()

            return redirect('bill_list')

    return render(request, 'hospital/admin/edit_bill.html', {
        'bill': bill,
        'items': items
    })

def delete_bill(request, pk):
    bill = get_object_or_404(Bills, id=pk)
    
    if request.method == "POST":
        bill.delete()
        return redirect('bill_list')
        
    return render(request, 'hospital/admin/confirm_delete_bill.html', {'bill': bill})

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
# doctor schedule fn
def doctor_schedule(request):

    doctor = Doctors.objects.get(user=request.user)

    schedules = DoctorSchedule.objects.filter(doctor=doctor)

    context = {
        'schedules': schedules
    }

    return render(request, 'hospital/doctor/doctor_schedule.html', context)
# add schedule fn
def add_schedule(request):

    doctor = Doctors.objects.get(user=request.user)

    if request.method == "POST":

        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_available = request.POST.get('is_available') == "True"

        DoctorSchedule.objects.create(
            doctor=doctor,
            day=day,
            start_time=start_time,
            end_time=end_time,
            is_available=is_available
        )

        messages.success(request, "Schedule added successfully!")

        return redirect('doctor_schedule')   

    return render(request, 'hospital/doctor/add_schedule.html')

# edit schedule
def edit_schedule(request, id):

    schedule = get_object_or_404(DoctorSchedule, id=id)

    if request.method == "POST":

        schedule.day = request.POST.get('day')
        schedule.start_time = request.POST.get('start_time')
        schedule.end_time = request.POST.get('end_time')
        schedule.is_available = request.POST.get('is_available') == "True"

        schedule.save()

        messages.success(request, "Schedule updated successfully!")

        return redirect('doctor_schedule')   

    context = {
        'schedule': schedule
    }

    return render(request, 'hospital/doctor/edit_schedule.html', context)

def delete_schedule(request, id):

    schedule = DoctorSchedule.objects.get(id=id)
    schedule.delete()

    messages.success(request, "Schedule deleted successfully")

    return redirect('doctor_schedule')


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

def doctor_dashboard(request):
    return render(request, 'hospital/doctor/doctor_dashboard.html')

def my_appointments(request):
    doctor = get_object_or_404(Doctors, user=request.user)
    
    today_all = Appointment.objects.filter(
        doctor=doctor, 
        appointment_date=date.today()
    ).order_by('token')

    # Upcoming appointments mein se Cancelled ko nikal dein
    upcoming_appointments = Appointment.objects.filter(
    doctor=doctor,
    appointment_date__gt=date.today()
    ).exclude(status='Cancelled').order_by('appointment_date', 'appointment_time')

    checked_patients = Appointment.objects.filter(
        doctor=doctor,
        status__in=['Completed', 'Cancelled', 'Billed'] 
    ).order_by('-appointment_date', '-appointment_time')
    
    current_serving_appt = today_all.filter(status='Serving').first()
    current_token = current_serving_appt.token if current_serving_appt else "0"

    context = {
        'today_appointments': today_all, 
        'upcoming_appointments': upcoming_appointments,
        'checked_patients': checked_patients,
        'current_token': current_token,
    }
    return render(request, 'hospital/doctor/my_appointments.html', context)

def next_token(request):
    doctor = get_object_or_404(Doctors, user=request.user)

    Appointment.objects.filter(
        doctor=doctor, 
        status='Serving', 
        appointment_date=date.today()
    ).update(status='Completed')
    
    next_patient = Appointment.objects.filter(
        doctor=doctor, 
        status='Pending', 
        appointment_date=date.today()
    ).order_by('token').first()
    
    if next_patient:
        next_patient.status = 'Serving'
        next_patient.save()
        return JsonResponse({'success': True, 'next_token': next_patient.token})
    
    return JsonResponse({'success': False, 'message': 'No more pending patients for today.'})

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

def add_medical_record(request):
    return render(request, 'hospital/doctor/add_medical_record.html' )

def patient_dashboard(request):
    return render(request, 'hospital/patient/patient_dashboard.html')

def appointments(request):
    try:
        profile = Patients.objects.get(user=request.user)
    except Patients.DoesNotExist:
        return redirect('signup')

    all_appointments = Appointment.objects.filter(patient_user=profile).order_by('-created_at')
    latest_active = all_appointments.filter(status__in=['Pending', 'Serving']).first()
    
    if latest_active:
        # 1. Get Current Serving Token
        serving_now = Appointment.objects.filter(
            doctor=latest_active.doctor,
            appointment_date=date.today(),
            status='Serving'
        ).first()
        
        current_val = serving_now.token if serving_now else 0
        if current_val == 0:
            last_completed = Appointment.objects.filter(
                doctor=latest_active.doctor,
                appointment_date=date.today(),
                status='Completed'
            ).order_by('-token').first()
            current_val = last_completed.token if last_completed else 0
            
        latest_active.current_serving = current_val

        # 2. Progress Calculation
        progress = 0
        if latest_active.token > 0:
            progress = (current_val / latest_active.token) * 100
            if progress > 100: progress = 100
        latest_active.progress_val = round(progress, 2)

        # 3. Smart Wait Time & Alert Logic
        show_alert = False
        if latest_active.status == 'Pending':
            # Token logic
            people_ahead = Appointment.objects.filter(
                doctor=latest_active.doctor,
                appointment_date=latest_active.appointment_date,
                status='Pending',
                token__lt=latest_active.token,
                token__gt=current_val
            ).count()
            token_wait = (people_ahead + 1) * 10

            # Clock logic
            now = datetime.now()
            appt_dt = datetime.combine(date.today(), latest_active.appointment_time)
            mins_left = int((appt_dt - now).total_seconds() / 60)

            # Assign wait time
            if 0 < mins_left < token_wait:
                latest_active.wait_time = mins_left
            elif mins_left <= 0:
                latest_active.wait_time = 2
            else:
                latest_active.wait_time = token_wait

            # Show Alert if 3 or fewer tokens away
            if 0 < (latest_active.token - current_val) <= 3:
                show_alert = True
        else:
            latest_active.wait_time = 0
        
        latest_active.show_alert = show_alert

    context = {
        'patient_appointments': all_appointments, 
        'latest_active': latest_active
    }
    return render(request, 'hospital/patient/appointments.html', context)

def get_live_update(request, appt_id):
    appointment = get_object_or_404(Appointment, id=appt_id)
    
    serving_now = Appointment.objects.filter(
        doctor=appointment.doctor,
        appointment_date=date.today(),
        status='Serving'
    ).first()
    
    current_val = serving_now.token if serving_now else 0
    if current_val == 0:
        last_done = Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=date.today(),
            status='Completed'
        ).order_by('-token').first()
        current_val = last_done.token if last_done else 0

    # Live Update Logic
    show_alert = False
    wait_time = 0
    if appointment.status == 'Pending':
        # Wait time
        people_ahead = Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=appointment.appointment_date,
            status='Pending',
            token__lt=appointment.token,
            token__gt=current_val
        ).count()
        token_wait = (people_ahead + 1) * 10
        
        now = datetime.now()
        appt_dt = datetime.combine(date.today(), appointment.appointment_time)
        mins_left = int((appt_dt - now).total_seconds() / 60)
        wait_time = mins_left if 0 < mins_left < token_wait else token_wait
        if mins_left <= 0: wait_time = 2

        # Alert
        if 0 < (appointment.token - current_val) <= 3:
            show_alert = True

    progress = 0
    if appointment.token > 0:
        progress = (current_val / appointment.token) * 100
        if progress > 100: progress = 100

    return JsonResponse({
        'current_serving': current_val,
        'wait_time': wait_time,
        'status': appointment.status,
        'progress': round(progress, 2),
        'show_alert': show_alert
    })

def cancel_appointment(request, pk):
    # 1. Pehle login user ki Patient Profile nikalen
    try:
        # Agar aapne model mein related_name='patient_profile' rakha hai
        patient_profile = request.user.patient_profile 
    except:
        # Alternate tareeqa agar related_name nahi hai
        patient_profile = get_object_or_404(Patients, user=request.user)

    # 2. Ab 'patient_user' mein patient_profile pass karein (request.user nahi)
    appointment = get_object_or_404(Appointment, id=pk, patient_user=patient_profile)
    
    if appointment.status == 'Pending':
        appointment.status = 'Cancelled'
        appointment.save()
        messages.success(request, f"Appointment #{appointment.token} has been cancelled.")
    else:
        messages.error(request, "You cannot cancel an appointment that is already serving or completed.")
        
    return redirect('appointments')

def appointment_form(request):
    # 1. Profile aur Age Fetching
    patient_profile = Patients.objects.filter(user=request.user).first()
    age = 0
    if patient_profile and patient_profile.dob:
        today = date.today()
        age = today.year - patient_profile.dob.year - ((today.month, today.day) < (patient_profile.dob.month, patient_profile.dob.day))

    if request.method == "POST":
        doc_id = request.POST.get('doctor')
        dept_id = request.POST.get('department')
        app_date_str = request.POST.get('appointment_date')
        
        # Date Validation
        app_date_obj = datetime.strptime(app_date_str, '%Y-%m-%d').date()
        day_name = app_date_obj.strftime('%A') 

        # Schedule Fetching
        schedule = DoctorSchedule.objects.filter(doctor_id=doc_id, day=day_name, is_available=True).first()

        if not schedule:
            messages.error(request, f"Doctor is not available on {day_name}.")
            return redirect('appointment_form')

        # --- SMART TIME & SLOT VALIDATION ---
        start_dt = datetime.combine(date.today(), schedule.start_time)
        end_dt = datetime.combine(date.today(), schedule.end_time)
        now = datetime.now()

        # Check A: Agar shift khatam ho chuki hai (For Today)
        if app_date_obj == date.today() and now >= end_dt:
            messages.error(request, f"Doctor's shift for today has already ended at {schedule.end_time.strftime('%I:%M %p')}.")
            return redirect('appointment_form')

        # Token Generation
        last_token = Appointment.objects.filter(
            doctor_id=doc_id, 
            appointment_date=app_date_str
        ).aggregate(Max('token'))['token__max'] or 0
        new_token = last_token + 1
        
        # Time Calculation (Base: 10 mins per patient)
        calculated_dt = start_dt + timedelta(minutes=last_token * 10)

        #Past Time Conflict Fix
        if app_date_obj == date.today() and calculated_dt < now:
            calculated_dt = now + timedelta(minutes=5)

        # STRICT SHIFT LIMIT 
        if calculated_dt > end_dt:
            messages.error(request, f"Sorry, all slots are full! Doctor's shift ends at {schedule.end_time.strftime('%I:%M %p')}.")
            return redirect('appointment_form')

        final_time = calculated_dt.time()

        # 3. Create Appointment
        Appointment.objects.create(
            patient_user=patient_profile,
            fullname=request.user.fullname,
            age=age,
            gender=patient_profile.gender,
            contact=patient_profile.phone,
            department_id=dept_id,
            doctor_id=doc_id,
            appointment_date=app_date_str,
            appointment_time=final_time,
            token=new_token
        )
        
        messages.success(request, f"Appointment Booked! Token: #{new_token} | Time: {final_time.strftime('%I:%M %p')}")
        return redirect('appointments')

    depts = Departments.objects.filter(status=True)
    context = {
        'departments': depts,
        'patient': patient_profile,
        'calculated_age': age
    }
    return render(request, 'hospital/patient/appointment-form.html', context)

def get_estimated_time(request):
    doc_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    
    if doc_id and date_str:
        try:
            app_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            day_name = app_date_obj.strftime('%A')
            schedule = DoctorSchedule.objects.filter(doctor_id=doc_id, day=day_name).first()
            
            if schedule:
                now = datetime.now()
                end_dt = datetime.combine(date.today(), schedule.end_time)
                
                # 1. Shift Check
                if app_date_obj == date.today() and now >= end_dt:
                    return JsonResponse({'success': False, 'message': 'Doctor\'s shift has ended for today.'})

                # 2. Time Calculation
                last_token = Appointment.objects.filter(doctor_id=doc_id, appointment_date=date_str).count()
                start_dt = datetime.combine(date.today(), schedule.start_time)
                calculated_dt = start_dt + timedelta(minutes=last_token * 10)

                if app_date_obj == date.today() and calculated_dt < now:
                    calculated_dt = now + timedelta(minutes=5)

                # 3. Final Slot Check
                if calculated_dt > end_dt:
                    return JsonResponse({'success': False, 'message': 'All slots are full for this doctor today.'})

                est_time = calculated_dt.strftime('%I:%M %p')
                return JsonResponse({'success': True, 'estimated_time': est_time})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error calculating time.'})
            
    return JsonResponse({'success': False})

def ajax_load_doctors(request):
    department_id = request.GET.get('department_id')
    # Sirf approved doctors jo us department ke hain
    doctors = Doctors.objects.filter(department_id=department_id, is_approved=True).values('id', 'user__fullname')
    return JsonResponse(list(doctors), safe=False)

def bill(request):

    try:
        # Agar aapne related_name='patient' nahi rakha to niche wala line error de sakti hai
        # Check karein aapke model mein related_name kya hai
        patient = Patients.objects.get(user=request.user) 
        bills = Bills.objects.filter(patient=patient)
    except Patients.DoesNotExist:
        # Agar user patient nahi hai (maslan admin hai) to empty list bhej dein ya error handle karein
        bills = []
        patient = None

    return render(request, 'hospital/patient/bill.html', {'bills': bills})

# =========================
# PATIENT BILL VIEWS
# =========================

def patient_bill_list(request):
    try:
        patient = Patients.objects.get(user=request.user)
        bills = Bills.objects.filter(patient=patient).order_by('-id')
    except Patients.DoesNotExist:
        bills = []

    return render(request, 'hospital/patient/patient_bill_list.html', {
        'bills': bills
    })


def patient_view_bill(request, pk):
    # Get bill
    bill = get_object_or_404(Bills, pk=pk)

    # Get related items (THIS WAS MISSING EARLIER)
    items = BillItems.objects.filter(bill=bill)

    # Send to template
    return render(request, 'hospital/patient/patient_view_bill.html', {
        'bill': bill,
        'items': items,
    })

def feedback(request):
    if request.method == "POST":
        description = request.POST.get('description')
        
        # 1. Pehle logged-in user ki Patient profile nikalen
        # (Assuming your related_name is 'patient_profile' or use the model name)
        try:
            patient_profile = request.user.patient_profile 
            
            # 2. Feedback save karte waqt profile object dein
            PatientFeedback.objects.create(
                patient=patient_profile,  # <--- SHI: Patient profile object
                description=description
            )
            messages.success(request, "Thank you! Your feedback has been submitted.")
            return redirect('feedback') # Ya jo bhi aapka page name hai
            
        except Patients.DoesNotExist:
            messages.error(request, "Patient profile not found. Please complete your profile.")
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

