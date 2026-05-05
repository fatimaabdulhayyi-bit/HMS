from django.shortcuts import render,redirect,get_object_or_404
from .models import UserAccount, Patients, Departments, Doctors, PatientFeedback, InPatient, DoctorSchedule, Appointment, Bills, BillItems,MedicalRecord
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Max
from datetime import date,datetime,timedelta
from django.db import transaction
from .decorators import role_required
from decimal import Decimal

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
    doctors = Doctors.objects.filter(is_approved=True)
    feedbacks = PatientFeedback.objects.select_related('patient__user').order_by('-created_at')[:5]


    context = {
        'total_patients': total_patients,
        'total_departments': total_departments,
        'departments': active_depts,
        'total_doctors' : total_doctors,
        'total_appointments': total_appointments,
        'doctors': doctors,
        'feedbacks': feedbacks

    }
    if request.user.is_authenticated:
        # User ke role ke mutabiq usay sahi dashboard par bhej do
        if request.user.role == 'doctor':
            return redirect('doctor_dashboard')
        elif request.user.role == 'patient':
            return redirect('patient_dashboard')
        elif request.user.role == 'admin':
            return redirect('admin_dashboard')
    return render(request, 'hospital/index.html', context)
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Pehle check karein ke fields khali toh nahi
        if not email or not password:
            messages.error(request, "Please provide both email and password.")
            return render(request, 'hospital/forms/login.html')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            # User mil gaya aur password sahi hai
            auth_login(request, user)

            # --- DOCTOR LOGIC ---
            if user.role == 'doctor':
                try:
                    doctor_profile = Doctors.objects.get(user=user)
                    if not user.is_approved or not doctor_profile.is_approved:
                        messages.warning(request, "Please wait for admin approval.")
                        return redirect('login')
                    return redirect('doctor_dashboard')
                except Doctors.DoesNotExist:
                    return redirect('doctorreg')

            # --- PATIENT LOGIC ---
            elif user.role == 'patient':
                patient_exists = Patients.objects.filter(user=user).exists()
                if not patient_exists:
                    return redirect('patientreg')
                return redirect('patient_dashboard')

            # --- ADMIN LOGIC ---
            elif user.role == 'admin' and user.is_admin:
                return redirect('admin_dashboard')
            
            else:
                return redirect('patient_dashboard')

        else:
            # --- ERROR HANDLING ---
            # Yahan check karte hain ke masla email mein hai ya password mein
            from hospital.models import UserAccount
            user_exists = UserAccount.objects.filter(email=email).exists()
            
            if not user_exists:
                messages.error(request, "Invalid Email: No account found with this email.")
            else:
                messages.error(request, "Invalid Password: The password you entered is incorrect.")
            
            return render(request, 'hospital/forms/login.html')

    return render(request, 'hospital/forms/login.html')

@role_required(allowed_roles=['patient'])
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

@role_required(allowed_roles=['doctor'])
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
        fee = request.POST.get('consultation_fee')

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
            experience=experience,
            consultation_fee=fee,
        )
        logout(request)
        messages.success(request, "Registration submitted successfully. Please wait for admin approval.")

        return redirect('login')

    return render(request, 'hospital/forms/doctorreg.html', {'departments': depts})

@role_required(allowed_roles=['admin'])
def department(request):
     # Database se saray patients ka data unke user account ke sath mangwana
    # select_related use karne se performance behtar hoti hai
    departments = Departments.objects.all()
    
    context = {
        'departments': departments
    }
    return render(request, 'hospital/admin/department.html', context)

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
def delete_department(request, pk):
    dept = get_object_or_404(Departments, id=pk)
    dept.delete()
    messages.success(request, "Department deleted!")
    return redirect('department')

@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    admin_user = UserAccount.objects.get(id=request.user.id)
    
    if request.method == 'POST':
        # --- 1. ADMIN PHOTO UPDATE ---
        if 'admin_photo' in request.FILES:
            uploaded_file = request.FILES.get('admin_photo')
            if uploaded_file.size <= 2 * 1024 * 1024:
                admin_user.profile_image = uploaded_file
                admin_user.save()
            return redirect('admin_dashboard')

        # --- 2. ADMIN PHOTO DELETE ---
        elif 'remove_admin_photo' in request.POST:
            if admin_user.profile_image:
                admin_user.profile_image.delete()
                admin_user.profile_image = None
                admin_user.save()
            return redirect('admin_dashboard')

    # --- DASHBOARD DATA ---
    context = {
        'total_patients': Patients.objects.count(),
        'total_doctors' : Doctors.objects.filter(is_approved=True).count(),
        'total_departments': Departments.objects.count(),
        'pending_doctors': Doctors.objects.filter(is_approved=False, user__is_active=True),
        'total_InPatients': InPatient.objects.filter(is_discharged=False).count(),
        'total_appointments': Appointment.objects.count(),
        'ongoing_appointments': Appointment.objects.filter(
            appointment_date=date.today(),
            status__in=['Pending', 'Serving']
        ).order_by('token')[:5],
    }
    
    return render(request, 'hospital/admin/admin_dashboard.html', context)
def view_doctors(request, id):
    doctor = get_object_or_404(Doctors, id=id)
    return render(request, 'hospital/admin/view_doctors.html', {'doctor': doctor})

def view_patient(request, id):
    patient = Patients.objects.get(id=id)   
    return render(request, 'hospital/admin/view_patient.html', {'patient': patient})

def view_ipd(request, id):
    ipd = InPatient.objects.get(id=id)
    return render(request, 'hospital/admin/view_ipd.html', {'ipd': ipd})

def view_department(request, id):
    department = Departments.objects.get(id=id)
    return render(request, 'hospital/admin/view_department.html', {'department': department})
@role_required(allowed_roles=['admin'])
def approve_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctors, id=doctor_id)

    doctor.is_approved = True
    doctor.save()
    
    user = doctor.user
    user.is_approved = True
    user.save()

    return redirect('admin_dashboard')

@role_required(allowed_roles=['admin'])
def reject_doctor(request, doctor_id):

    doctor = get_object_or_404(Doctors, id=doctor_id)
    user = doctor.user

    doctor.delete()
    user.delete()    # Delete user account
    return redirect('admin_dashboard')

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
def add_appointment(request):
    if request.method == "POST":
        # Form data fetch karein
        patient_id = request.POST.get('patient')
        doc_id = request.POST.get('doctor')
        dept_id = request.POST.get('department')
        app_date_str = request.POST.get('appointment_date')
        
        # 1. Patient Profile & Age Fetching
        patient_profile = get_object_or_404(Patients, id=patient_id)
        doctor = get_object_or_404(Doctors, id=doc_id)
        
        age = 0
        if patient_profile.dob:
            today = date.today()
            age = today.year - patient_profile.dob.year - ((today.month, today.day) < (patient_profile.dob.month, patient_profile.dob.day))

        # 2. Schedule & Date Validation
        app_date_obj = datetime.strptime(app_date_str, '%Y-%m-%d').date()
        day_name = app_date_obj.strftime('%A') 
        schedule = DoctorSchedule.objects.filter(doctor_id=doc_id, day=day_name, is_available=True).first()

        if not schedule:
            messages.error(request, f"Doctor is not available on {day_name}.")
            return redirect('add_appointment')

        # 3. Smart Time Calculation (Patient side logic)
        start_dt = datetime.combine(date.today(), schedule.start_time)
        end_dt = datetime.combine(date.today(), schedule.end_time)
        now = datetime.now()

        total_booked = Appointment.objects.filter(
            doctor_id=doc_id, 
            appointment_date=app_date_str
        ).count()
        
        calculated_dt = start_dt + timedelta(minutes=total_booked * 10)

        # Past time conflict fix
        if app_date_obj == date.today() and calculated_dt < now:
            calculated_dt = now + timedelta(minutes=5)

        if calculated_dt > end_dt:
            messages.error(request, "Sorry, all slots are full for this shift!")
            return redirect('add_appointment')

        final_time = calculated_dt.time()

        # 4. --- TRANSACTION BLOCK (Atomic) ---
        # Same as patient_form logic
        try:
            with transaction.atomic():
                # A. Create Appointment (Token is None)
                appointment = Appointment.objects.create(
                    patient_user=patient_profile,
                    fullname=patient_profile.user.fullname,
                    age=age,
                    gender=patient_profile.gender,
                    contact=patient_profile.phone,
                    department_id=dept_id,
                    doctor=doctor,
                    appointment_date=app_date_str,
                    appointment_time=final_time,
                    token=None,  # Token None rahy ga jab tak pay na ho
                    status='Pending'
                )

                # B. AUTO-BILL: System bill generate kare ga
                bill = Bills.objects.create(
                    patient=patient_profile,
                    patient_type='Out-Patient',
                    bill_date=date.today(),
                    subtotal=doctor.consultation_fee,
                    grand_total=doctor.consultation_fee,
                    payment_status='Unpaid'
                )

                # C. Bill Item add karein
                BillItems.objects.create(
                    bill=bill,
                    service_name=f"Consultation Fee - Dr. {doctor.user.fullname}",
                    quantity=1,
                    unit_price=doctor.consultation_fee,
                    total=doctor.consultation_fee
                )

            messages.success(request, f"Appointment Added! Bill of Rs.{doctor.consultation_fee} generated. Token will be assigned after payment.")
            return redirect('manage_appointments')

        except Exception as e:
            messages.error(request, f"Database Error: {str(e)}")
            return redirect('add_appointment')

    # GET Request
    context = {
        'patients': Patients.objects.all(),
        'departments': Departments.objects.filter(status=True),
        'doctors': Doctors.objects.filter(is_approved=True),
    }
    return render(request, 'hospital/admin/add_appointment.html', context)

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
def generate_bills(request, p_type=None, id=None):
    selected_patient = None
    initial_type = ""
    source_obj = None
    
    # URL parameters se patient fetch karna
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
                # POST data se patient retrieval
                p_id = request.POST.get('patient')
                patient_obj = get_object_or_404(Patients, id=p_id)
                p_status = request.POST.get('payment_status')
                
                # Main Bill Create karna
                bill = Bills.objects.create(
                    patient=patient_obj,
                    patient_type=request.POST.get('patient_type'),
                    bill_date=request.POST.get('bill_date') or date.today(),
                    admission_date=request.POST.get('admission_date') or None,
                    discharge_date=request.POST.get('discharge_date') or None,
                    staying_days=int(request.POST.get('staying_days') or 0),
                    payment_status=p_status,
                    payment_method=request.POST.get('payment_method') if p_status == "Paid" else "Unpaid",
                    amount_paid=Decimal(request.POST.get('amount_paid') or 0) if p_status == "Paid" else 0,
                    grand_total=0 
                )

                # Dynamic Items Process karna
                services = request.POST.getlist('service_name[]')
                qtys = request.POST.getlist('qty[]')
                prices = request.POST.getlist('unit_price[]')
                discounts = request.POST.getlist('discount[]')

                total_sub = Decimal('0.00')
                total_disc = Decimal('0.00')

                for i in range(len(services)):
                    s_name = services[i].strip()
                    if not s_name: continue

                    q = int(qtys[i] or 1)
                    p = Decimal(prices[i] or 0)
                    d = Decimal(discounts[i] or 0)
                    
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

                # Bill Totals Update
                bill.subtotal = total_sub
                bill.total_discount = total_disc
                bill.grand_total = max(0, total_sub - total_disc)
                bill.save()
                
                # Dashboard status update
                if p_type == 'OPD':
                    Appointment.objects.filter(id=id).update(status='Billed') 
                elif p_type == 'IPD':
                    InPatient.objects.filter(id=id).update(status='Billed', is_discharged=True)

                messages.success(request, f"Bill #{bill.id} generated successfully!")
                return redirect('bill_list')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    context = {
        'patients': Patients.objects.all(),
        'selected_patient': selected_patient,
        'initial_type': initial_type,
        'source_obj': source_obj,
    }
    return render(request, 'hospital/admin/generate_bills.html', context)

@role_required(allowed_roles=['admin'])
def bill_list(request):
    bills = Bills.objects.all().order_by('-created_at')
    return render(request, 'hospital/admin/bill_list.html', {'bills': bills})

@role_required(allowed_roles=['admin'])
def view_bill(request, pk):
    # 1. Pehle Bill nikalein
    bill = get_object_or_404(Bills, id=pk)
    items = BillItems.objects.filter(bill=bill)
    context = {
        'bill': bill,
        'items': items  
    }
    return render(request, 'hospital/admin/view_bill.html', context)

@role_required(allowed_roles=['admin'])
def edit_bill(request, pk):
    bill = get_object_or_404(Bills, id=pk)
    
    # --- SECURITY CHECK ---
    # Agar bill pehle se hi 'Paid' hai, toh edit allow nahi karna
    if bill.payment_status == 'Paid':
        messages.warning(request, "Paid bills cannot be edited for security reasons.")
        return redirect('bill_list')
    # ----------------------

    items = BillItems.objects.filter(bill=bill)

    if request.method == "POST":
        old_status = bill.payment_status
        new_status = request.POST.get('payment_status')

        try:
            with transaction.atomic():
                bill.bill_date = request.POST.get('bill_date')
                bill.payment_status = new_status
                bill.payment_method = request.POST.get('payment_method')
                
                if bill.patient_type == "In-Patient":
                    bill.discharge_date = request.POST.get('discharge_date')
                    bill.staying_days = int(request.POST.get('staying_days') or 1)

                # Items refresh (Delete and Re-create)
                items.delete()
                
                service_names = request.POST.getlist('service_name[]')
                quantities = request.POST.getlist('qty[]')
                unit_prices = request.POST.getlist('unit_price[]')
                discounts = request.POST.getlist('discount[]')

                t_sub = Decimal('0.00')
                t_disc = Decimal('0.00')

                for i in range(len(service_names)):
                    q = int(quantities[i])
                    p = Decimal(unit_prices[i])
                    d = Decimal(discounts[i])
                    row_total = max(0, (q * p) - d)

                    BillItems.objects.create(
                        bill=bill,
                        service_name=service_names[i],
                        quantity=q,
                        unit_price=p,
                        discount=d,
                        total=row_total
                    )
                    t_sub += (q * p)
                    t_disc += d

                bill.subtotal = t_sub
                bill.total_discount = t_disc
                bill.grand_total = max(0, t_sub - t_disc)
                
                # Payment calculation
                bill.amount_paid = bill.grand_total if new_status == 'Paid' else 0
                bill.save()

                # TOKEN ASSIGNMENT LOGIC (Sirf tab jab status Unpaid se Paid ho raha ho)
                if new_status == 'Paid' and old_status != 'Paid':
                    # Apne model naming convention ke mutabiq check karein (patient ya patient_user)
                    appt = Appointment.objects.filter(patient_user=bill.patient, token__isnull=True).order_by('-created_at').first()
                    if appt:
                        last_t = Appointment.objects.filter(
                            doctor=appt.doctor, 
                            appointment_date=appt.appointment_date
                        ).aggregate(Max('token'))['token__max'] or 0
                        
                        appt.token = last_t + 1
                        appt.status = 'Pending'
                        appt.save()
                        messages.success(request, f"Bill Paid & Token #{appt.token} Assigned Successfully.")
                    else:
                        messages.info(request, "Bill Paid. No pending appointment found to assign token.")
                else:
                    messages.success(request, "Bill Updated Successfully.")

                return redirect('bill_list')
        except Exception as e:
            messages.error(request, f"Update Error: {str(e)}")

    return render(request, 'hospital/admin/edit_bill.html', {'bill': bill, 'items': items})

@role_required(allowed_roles=['admin'])
def delete_bill(request, pk):
    bill = get_object_or_404(Bills, id=pk)
    
    if request.method == "POST":
        bill.delete()
        return redirect('bill_list')
        
    return render(request, 'hospital/admin/confirm_delete_bill.html', {'bill': bill})

@role_required(allowed_roles=['admin'])
def doctors(request):
    all_doctors = Doctors.objects.filter(is_approved=True) 
    return render(request, 'hospital/admin/doctors.html', {'doctors': all_doctors})

@role_required(allowed_roles=['admin'])
def add_doctor(request):
    if request.method == "POST":
        email = request.POST.get('email')
        fullname = request.POST.get('fullname')
        password = "Doctor@123"  # Default password

        try:
            # 1. Email duplication check
            if UserAccount.objects.filter(email=email).exists():
                messages.error(request, "This email is already registered.")
                return redirect('add_doctor')

            # 2. UserAccount create karein
            user = UserAccount.objects.create_user(
                email=email, 
                password=password, 
                fullname=fullname, 
                role='doctor'
            )
            
            # CRITICAL FIX: Admin add kar raha hai toh user level approval true karein
            user.is_approved = True 
            user.save()

            # 3. Department object get karein
            dept_id = request.POST.get('dept')
            dept_obj = Departments.objects.get(id=dept_id) if dept_id else None
            
            fee = request.POST.get('consultation_fee')
            # 4. Check status from form
            status_check = request.POST.get('is_approved') == 'True'

            # 5. Doctors Profile create karein
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
                consultation_fee=fee,
                is_approved=status_check # Profile level approval
            )
            
            messages.success(request, f"Doctor {fullname} created successfully and approved!")
            return redirect('doctors')
            
        except Exception as e:
            print(f"Error creating doctor: {e}") 
            messages.error(request, f"Registration failed: {str(e)}")

    depts = Departments.objects.filter(status=True)
    return render(request, 'hospital/admin/add_doctor.html', {'departments': depts})

@role_required(allowed_roles=['admin'])
def update_doctor(request, pk):
    doctor = get_object_or_404(Doctors, id=pk)
    depts = Departments.objects.filter(status=True)

    if request.method == "POST":
        try:
            # Basic Details
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
            
            # FEE FIX: Make sure your model field is 'consultation_fee'
            doctor.consultation_fee = request.POST.get('consultation_fee')
            
            # Status update
            doctor.is_approved = request.POST.get('is_approved') == 'True'

            doctor.save()
            messages.success(request, f"Dr. {doctor.user.fullname}'s details updated.")
            return redirect('doctors')

        except Exception as e:
            messages.error(request, f"Update failed: {e}")
            # Fix redirect with PK
            return redirect('update_doctor', pk=pk)

    return render(request, 'hospital/admin/update_doctor.html', {
        'doctor': doctor, 
        'departments': depts
    })

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['doctor'])
def doctor_schedule(request):

    doctor = Doctors.objects.get(user=request.user)

    schedules = DoctorSchedule.objects.filter(doctor=doctor)

    context = {
        'schedules': schedules
    }

    return render(request, 'hospital/doctor/doctor_schedule.html', context)

@role_required(allowed_roles=['doctor'])
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

@role_required(allowed_roles=['doctor'])
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

@role_required(allowed_roles=['doctor'])
def delete_schedule(request, id):

    schedule = DoctorSchedule.objects.get(id=id)
    schedule.delete()

    messages.success(request, "Schedule deleted successfully")

    return redirect('doctor_schedule')

@role_required(allowed_roles=['admin'])
def patients(request):
    # Database se saray patients ka data unke user account ke sath mangwana
    # select_related use karne se performance behtar hoti hai
    patients = Patients.objects.all().select_related('user')
    
    context = {
        'patients': patients
    }
    return render(request, 'hospital/admin/patients.html', context)

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
def In_Patient(request):
    # 'ipd_records' variable name use kiya hai jo template mein loop ho raha hai
    records = InPatient.objects.all().order_by('-admission_date')
    return render(request, 'hospital/admin/In_patient.html', {'ipd_records': records})

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
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

@role_required(allowed_roles=['admin'])
def discharge_patient(request, pk):
    record = get_object_or_404(InPatient, pk=pk)
    record.is_discharged = True
    record.save()
    messages.success(request, f"{record.patient.user.fullname} has been discharged.")
    return redirect('In_Patient')

@role_required(allowed_roles=['doctor'])
def doctor_dashboard(request):
    return render(request, 'hospital/doctor/doctor_dashboard.html')

@role_required(allowed_roles=['doctor'])
def my_appointments(request):
    doctor = get_object_or_404(Doctors, user=request.user)
    
    # FILTER FIX: Sirf wo appointments dikhayen jin ka Token generate ho chuka hai
    today_all = Appointment.objects.filter(
        doctor=doctor, 
        appointment_date=date.today(),
        token__isnull=False # <--- Ye line unpaid/untokenized logo ko filter kar degi
    ).order_by('token')

    # Baki queries same raheingi...
    upcoming = Appointment.objects.filter(doctor=doctor, appointment_date__gt=date.today()).exclude(status='Cancelled')
    checked = Appointment.objects.filter(doctor=doctor, status__in=['Completed', 'Cancelled', 'Billed']).order_by('-token')

    context = {
        'today_appointments': today_all, 
        'upcoming_appointments': upcoming,
        'checked_patients': checked,
        'current_token': today_all.filter(status='Serving').first().token if today_all.filter(status='Serving').exists() else "0",
    }
    return render(request, 'hospital/doctor/my_appointments.html', context)

@role_required(allowed_roles=['doctor'])
def next_token(request):
    doctor = get_object_or_404(Doctors, user=request.user)
    today_name = date.today().strftime('%A')
    now_time = datetime.now().time()

    # 1. Clinic Schedule Check
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor, 
        day=today_name, 
        is_available=True
    ).first()
    
    if not schedule:
        return JsonResponse({
            'success': False, 
            'message': 'You do not have a schedule for today.'
        })
    
    if now_time < schedule.start_time:
        return JsonResponse({
            'success': False, 
            'message': f'your time starts at {schedule.start_time.strftime("%I:%M %p")}. Cannot start early.'
        })

    # 2. Purane serving ko Complete karein
    Appointment.objects.filter(
        doctor=doctor, 
        status='Serving', 
        appointment_date=date.today()
    ).update(status='Completed')
    
    # 3. Next pending patient fetch karein
    next_patient = Appointment.objects.filter(
        doctor=doctor, 
        status='Pending', 
        appointment_date=date.today()
    ).order_by('token').first()
    
    if next_patient:
        next_patient.status = 'Serving'
        next_patient.save()
        return JsonResponse({
            'success': True, 
            'next_token': next_patient.token
        })
    
    return JsonResponse({
        'success': False, 
        'message': 'No more pending patients for today.'
    })

@role_required(allowed_roles=['doctor'])
def profiledoc(request):
    doctor = Doctors.objects.filter(user=request.user).select_related('user').first()
    user_obj = request.user
    
    if request.method == 'POST':
        # 1. AUTO-UPLOAD LOGIC
        if 'photo' in request.FILES:
            uploaded_file = request.FILES.get('photo')
            if uploaded_file.size <= 2 * 1024 * 1024:
                user_obj.profile_image = uploaded_file
                user_obj.save()
            else:
                messages.error(request, "Image size too large! Max 2MB allowed.")
            return redirect('profiledoc')

        # 2. DELETE IMAGE LOGIC
        elif 'remove_photo' in request.POST:
            if user_obj.profile_image:
                user_obj.profile_image.delete() # Media folder se file remove karega
                user_obj.profile_image = None
                user_obj.save()
            return redirect('profiledoc')

    context = {
        'doctor': doctor
    }
    return render(request, 'hospital/doctor/profiledoc.html', context)

@role_required(allowed_roles=['doctor'])
def edit_docprofile(request):
    doctor = get_object_or_404(Doctors, user=request.user)
    all_departments = Departments.objects.all()

    if request.method == "POST":
        # ... (baaki fields same rahenge) ...
        doctor.father_name = request.POST.get('father_name')
        doctor.dob = request.POST.get('dob')
        doctor.gender = request.POST.get('gender')
        doctor.cnic = request.POST.get('cnic')
        doctor.phone = request.POST.get('phone')
        doctor.address = request.POST.get('address')
        
        # NAYA FIELD: Consultation Fee
        doctor.consultation_fee = request.POST.get('consultation_fee')
        
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

@role_required(allowed_roles=['doctor'])
def view_medical_record(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # 1. Is specific appointment ka record (agar doctor ne save kiya hai)
    medical_record = MedicalRecord.objects.filter(appointment=appointment).first()
    
    # 2. Patient ki mukammal history (Life-time records)
    # appointment.patient_user (Patients model) -> .user (UserAccount model)
    patient_account = appointment.patient_user.user
    full_history = MedicalRecord.objects.filter(patient=patient_account).order_by('-created_at')

    return render(request, 'hospital/doctor/view_medical_record.html', {
        'appointment': appointment,
        'medical_record': medical_record,
        'full_history': full_history,
    })

@role_required(allowed_roles=['doctor'])
def add_medical_record(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        # 1. Appointment se patient (UserAccount object) nikalna
        # patient_user 'Patients' model hai, uske andar 'user' field 'UserAccount' hai
        patient_account = appointment.patient_user.user 
        
        # 2. Doctor (request.user) jo ke already UserAccount object hai
        doctor_account = request.user 

        # Record create karna
        MedicalRecord.objects.create(
            appointment=appointment,
            patient=patient_account,  # UserAccount object assigned
            doctor=doctor_account,    # UserAccount object assigned
            symptoms=request.POST.get('symptoms'),
            diagnosis=request.POST.get('diagnosis'),
            tests=request.POST.get('tests'),
            medicines_data=[
                {"name": n, "dosage": d} 
                for n, d in zip(request.POST.getlist('med_name[]'), request.POST.getlist('med_dosage[]')) 
                if n
            ]
        )
        
        messages.success(request, "Record Added Successfully!")
        return redirect('view_medical_record', appointment_id=appointment_id)

    return render(request, 'hospital/doctor/add_medical_record.html', {'appointment': appointment})

@role_required(allowed_roles=['doctor'])
def edit_medical_record(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    medical_record = get_object_or_404(MedicalRecord, appointment=appointment)

    if request.method == 'POST':
        medical_record.symptoms = request.POST.get('symptoms')
        medical_record.diagnosis = request.POST.get('diagnosis')
        medical_record.tests = request.POST.get('tests')
        medical_record.medicines_data = [{"name": n, "dosage": d} for n, d in zip(request.POST.getlist('med_name[]'), request.POST.getlist('med_dosage[]')) if n]
        medical_record.save()
        messages.success(request, "Record Updated!")
        return redirect('view_medical_record', appointment_id=appointment_id)

    return render(request, 'hospital/doctor/edit_medical_record.html', {
        'appointment': appointment,
        'medical_record': medical_record
    })

@role_required(allowed_roles=['patient'])
def patient_dashboard(request):
    return render(request, 'hospital/patient/patient_dashboard.html')

@role_required(allowed_roles=['patient'])
def appointments(request):
    try:
        profile = Patients.objects.get(user=request.user)
    except Patients.DoesNotExist:
        return redirect('signup')

    all_appointments = Appointment.objects.filter(patient_user=profile).order_by('-created_at')
    
    latest_active = all_appointments.filter(
        appointment_date=date.today(), 
        status__in=['Pending', 'Serving']
    ).first()
    
    if latest_active and latest_active.token is not None:
        now = datetime.now()
        now_time = now.time()
        today_day = now.strftime('%A') 

        # 1. Doctor schedule logic
        schedule = DoctorSchedule.objects.filter(doctor=latest_active.doctor, day=today_day).first()
        doctor_start_time = schedule.start_time if schedule else None

        # 2. Serving Token Logic
        serving_now = Appointment.objects.filter(
            doctor=latest_active.doctor,
            appointment_date=date.today(),
            status='Serving'
        ).first()
        
        if serving_now and serving_now.token is not None:
            current_val = serving_now.token
        else:
            last_completed = Appointment.objects.filter(
                doctor=latest_active.doctor,
                appointment_date=date.today(),
                status='Completed'
            ).exclude(token__isnull=True).order_by('-token').first()
            current_val = last_completed.token if last_completed else 0
            
        latest_active.current_serving = current_val

        # 3. Wait Time & Alert Logic
        show_alert = False
        if latest_active.status == 'Pending':
            if doctor_start_time and now_time < doctor_start_time:
                latest_active.wait_time = "Doctor not started yet"
            else:
                people_ahead = Appointment.objects.filter(
                    doctor=latest_active.doctor,
                    appointment_date=latest_active.appointment_date,
                    status='Pending',
                    token__lt=latest_active.token,
                    token__gt=current_val
                ).count()
                
                if latest_active.appointment_time:
                    appt_dt = datetime.combine(date.today(), latest_active.appointment_time)
                    mins_remaining = int((appt_dt - now).total_seconds() / 60)
                else:
                    mins_remaining = 30

                token_wait = (people_ahead + 1) * 10
                wait_val = mins_remaining if 0 < mins_remaining < token_wait else token_wait
                if mins_remaining <= 0: wait_val = 2
                
                # Check Alert Condition
                token_gap = latest_active.token - current_val
                if 0 < token_gap <= 3 and mins_remaining <= 20:
                    show_alert = True
                    latest_active.wait_time = "Be Ready! Almost your turn."
                else:
                    latest_active.wait_time = f"{wait_val} mins"
        
        elif latest_active.status == 'Serving':
            latest_active.wait_time = "In Progress"
        
        latest_active.show_alert = show_alert

        # Progress Calculation
        progress = 0
        if latest_active.token > 0:
            progress = (current_val / latest_active.token) * 100
            if progress > 100: progress = 100
        latest_active.progress_val = round(progress, 2)

    elif latest_active:
        latest_active.wait_time = "Token Pending (Pay Bill)"
        latest_active.current_serving = 0
        latest_active.progress_val = 0

    context = {
        'patient_appointments': all_appointments, 
        'latest_active': latest_active,
        'today': date.today()
    }
    return render(request, 'hospital/patient/appointments.html', context)


@role_required(allowed_roles=['patient'])
def get_live_update(request, appt_id):
    appointment = get_object_or_404(Appointment, id=appt_id)
    now = datetime.now()
    now_time = now.time()
    today_day = now.strftime('%A')
    
    if appointment.appointment_date != date.today():
        return JsonResponse({'current_serving': 0, 'wait_time': "Scheduled", 'status': appointment.status, 'progress': 0, 'show_alert': False})

    schedule = DoctorSchedule.objects.filter(doctor=appointment.doctor, day=today_day).first()
    doctor_start_time = schedule.start_time if schedule else None

    serving_now = Appointment.objects.filter(
        doctor=appointment.doctor,
        appointment_date=date.today(),
        status='Serving'
    ).first()
    
    if serving_now:
        current_val = serving_now.token
    else:
        last_done = Appointment.objects.filter(
            doctor=appointment.doctor,
            appointment_date=date.today(),
            status='Completed'
        ).order_by('-token').first()
        current_val = last_done.token if last_done else 0

    show_alert = False
    wait_time_display = "0"
    
    if appointment.status == 'Pending':
        if doctor_start_time and now_time < doctor_start_time:
            wait_time_display = "Doctor not started yet"
        else:
            people_ahead = Appointment.objects.filter(
                doctor=appointment.doctor,
                appointment_date=appointment.appointment_date,
                status='Pending',
                token__lt=appointment.token,
                token__gt=current_val
            ).count()
            
            token_wait = (people_ahead + 1) * 10
            appt_dt = datetime.combine(date.today(), appointment.appointment_time)
            mins_remaining = int((appt_dt - now).total_seconds() / 60)
            
            res_wait = mins_remaining if 0 < mins_remaining < token_wait else token_wait
            if mins_remaining <= 0: res_wait = 2

            # Alert Check
            token_gap = appointment.token - current_val
            if 0 < token_gap <= 3 and mins_remaining <= 20:
                show_alert = True
                wait_time_display = "Be Ready! Almost your turn."
            else:
                wait_time_display = f"{res_wait} mins"
    
    elif appointment.status == 'Serving':
        wait_time_display = "In Progress"

    progress = 0
    if appointment.token > 0:
        progress = (current_val / appointment.token) * 100
        if progress > 100: progress = 100

    return JsonResponse({
        'current_serving': current_val,
        'wait_time': wait_time_display,
        'status': appointment.status,
        'progress': round(progress, 2),
        'show_alert': show_alert
    })

@role_required(allowed_roles=['patient'])
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

@role_required(allowed_roles=['patient'])
def appointment_form(request):
    # 1. Profile aur Age Fetching (Sahi variables set karein)
    patient_profile = Patients.objects.filter(user=request.user).first()
    age = 0
    if patient_profile and patient_profile.dob:
        today = date.today()
        age = today.year - patient_profile.dob.year - ((today.month, today.day) < (patient_profile.dob.month, patient_profile.dob.day))

    if request.method == "POST":
        doc_id = request.POST.get('doctor')
        dept_id = request.POST.get('department')
        app_date_str = request.POST.get('appointment_date')
        
        doctor = get_object_or_404(Doctors, id=doc_id)
        
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

        # Check A: Shift end check
        if app_date_obj == date.today() and now >= end_dt:
            messages.error(request, f"Doctor's shift for today has ended at {schedule.end_time.strftime('%I:%M %p')}.")
            return redirect('appointment_form')

        # Appointment Count for Time Calculation (Token abhi generate nahi ho raha)
        total_booked = Appointment.objects.filter(
            doctor_id=doc_id, 
            appointment_date=app_date_str
        ).count()
        
        calculated_dt = start_dt + timedelta(minutes=total_booked * 10)

        if app_date_obj == date.today() and calculated_dt < now:
            calculated_dt = now + timedelta(minutes=5)

        if calculated_dt > end_dt:
            messages.error(request, "Sorry, all slots are full for this shift!")
            return redirect('appointment_form')

        final_time = calculated_dt.time()

        # --- TRANSACTION BLOCK (Atomic) ---
        try:
            with transaction.atomic():
                # 1. Create Appointment (Token = None for Pay-First)
                appointment = Appointment.objects.create(
                    patient_user=patient_profile,
                    fullname=request.user.fullname,
                    age=age,
                    gender=patient_profile.gender,
                    contact=patient_profile.phone,
                    department_id=dept_id,
                    doctor=doctor,
                    appointment_date=app_date_str,
                    appointment_time=final_time,
                    token=None,  # Pay-First logic
                    status='Pending'
                )

                # 2. AUTO-BILL: System khud bill banaye ga
                bill = Bills.objects.create(
                    patient=patient_profile,
                    patient_type='Out-Patient',
                    bill_date=date.today(),
                    subtotal=doctor.consultation_fee,
                    grand_total=doctor.consultation_fee,
                    payment_status='Unpaid'
                )

                # 3. Bill Item add karein
                BillItems.objects.create(
                    bill=bill,
                    service_name=f"Consultation Fee - Dr. {doctor.user.fullname}",
                    quantity=1,
                    unit_price=doctor.consultation_fee,
                    total=doctor.consultation_fee
                )

            messages.success(request, f"Request Sent! Please pay Rs.{doctor.consultation_fee} at reception to get your token.")
            return redirect('appointments')

        except Exception as e:
            messages.error(request, f"Database Error: {str(e)}")
            return redirect('appointment_form')

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

@role_required(allowed_roles=['patient'])
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

@role_required(allowed_roles=['patient'])
def pay_bill(request, pk):
    bill = get_object_or_404(Bills, id=pk, patient__user=request.user)
    
    if bill.payment_status == 'Paid':
        messages.info(request, "This bill is already paid.")
    else:
        bill.payment_status = 'Paid'
        bill.payment_method = 'Online'
        bill.amount_paid = bill.grand_total
        bill.save()

        # --- TOKEN GENERATION START ---
        # Patient ki latest appointment uthayein jis ka token None hai
        appointment = Appointment.objects.filter(
            patient_user=bill.patient, 
            token__isnull=True
        ).order_by('-created_at').first() # Sab se latest wali

        if appointment:
            # Aaj ke din is doctor ka max token
            last_token_record = Appointment.objects.filter(
                doctor=appointment.doctor,
                appointment_date=appointment.appointment_date # Use appointment's date
            ).aggregate(Max('token'))
            
            last_val = last_token_record['token__max']
            new_token = (last_val + 1) if last_val is not None else 1
            
            appointment.token = new_token
            appointment.status = 'Pending'
            appointment.save()
            
            messages.success(request, f"Payment Successful! Your Token is {new_token}")
        else:
            # Agar appointment direct nahi mil rahi to check karein model fields
            messages.warning(request, "Payment received but no pending appointment found to assign token.")
        # --- TOKEN GENERATION END ---

    return redirect('bill')

@role_required(allowed_roles=['patient'])
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

@role_required(allowed_roles=['patient'])
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

@role_required(allowed_roles=['patient'])
def medical_records(request):
    # Sirf login patient ke records nikalna
    # request.user.patient_profile se hum Patients model tak pohanchtay hain
    records = MedicalRecord.objects.filter(patient=request.user).order_by('-created_at')
    
    return render(request, 'hospital/patient/medical_records.html', {'records': records})

@role_required(allowed_roles=['patient'])
def profile(request):
    # Patients model se data get karna
    patient = Patients.objects.filter(user=request.user).select_related('user').first()
    user_obj = patient.user 
    
    if request.method == 'POST':
        # Agar photo select ki gayi hai (Auto-upload via JS)
        if 'photo' in request.FILES:
            uploaded_file = request.FILES.get('photo')
            if uploaded_file.size <= 2 * 1024 * 1024:
                user_obj.profile_image = uploaded_file
                user_obj.save()
            else:
                messages.error(request, "Image size too large!")
            return redirect('profile')

        # Agar Delete button click kiya gaya hai
        elif 'remove_photo' in request.POST:
            if user_obj.profile_image:
                user_obj.profile_image.delete()
                user_obj.profile_image = None
                user_obj.save()
            return redirect('profile')

    return render(request, 'hospital/patient/profile.html', {'patient': patient})

@role_required(allowed_roles=['patient'])
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
    return redirect('index')