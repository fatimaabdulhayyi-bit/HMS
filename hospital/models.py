from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserAccountManager(BaseUserManager):
    def create_user(self, email, fullname, role, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, fullname=fullname, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, fullname, password=None):
        """
        Superuser creation: role automatically 'admin'
        """
        user = self.create_user(email=email, fullname=fullname, role='admin', password=password)
        user.is_admin = True
        user.is_superadmin=True
        user.is_approved = True
        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    ]

    fullname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)  # Doctor approval flag

    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']  # role removed to avoid prompt in createsuperuser

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.fullname} | {self.email} | {self.role}"

    # Permissions for admin
    @property
    def is_staff(self):
        return self.is_superadmin

    def has_perm(self, perm, obj=None):
        return self.is_superadmin

    def has_module_perms(self, app_label):
        return self.is_superadmin
    
class Patients(models.Model):
    # 'user' field connects this to UserAccount table (One-to-One)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='patient_profile')
    
    guardian_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    cnic = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    blood_group = models.CharField(max_length=5)
    
    PATIENT_TYPES = [
        ('OPD', 'OPD'),
        ('IPD', 'IPD'),
    ]
    patient_type = models.CharField(max_length=10, choices=PATIENT_TYPES, default='OPD')
    status = models.CharField(max_length=10, default='Active')

    class Meta:
        db_table = 'Patients'
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.user.fullname} | {self.patient_type}"


class Departments(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=100, blank=True, null=True)
    status = models.BooleanField(default=True) # Active=True, Inactive=False

    class Meta:
        db_table = 'Departments'

    def __str__(self):
        return f"{self.name} | {self.description}"

class Doctors(models.Model):

    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)

    father_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    cnic = models.CharField(max_length=20)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    department = models.ForeignKey(Departments, on_delete=models.SET_NULL, null=True)

    license_number = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100)
    experience = models.IntegerField()
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_approved = models.BooleanField(default=False)

    class Meta:
        db_table = "Doctors"
        verbose_name_plural = "Doctors"

    def __str__(self):
        return self.user.fullname


class DoctorSchedule(models.Model):

    doctor = models.ForeignKey(Doctors, on_delete=models.CASCADE)

    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "DoctorSchedule"

    def __str__(self):
        return f"{self.doctor} - {self.day}"
    
class PatientFeedback(models.Model):
    # Kaunsa patient feedback de raha hai (Login user)
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.patient.user.fullname} | {self.description}"

class InPatient(models.Model):

    STATUS_CHOICES = [
        ('Admitted', 'Admitted'),
        ('Discharge', 'Discharge'),
        ('Billed', 'Billed')
    ]

    patient = models.ForeignKey(Patients, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctors, on_delete=models.CASCADE)
    room_no = models.CharField(max_length=50)
    bed_no = models.CharField(max_length=50)
    admission_date = models.DateField()
    admission_time = models.TimeField()
    diagnosis = models.TextField()
    is_discharged = models.BooleanField(default=False)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='Admitted')
    
    # Meta class taake data sorted rahay
    class Meta:
        db_table = "In-Patietns"
        verbose_name_plural = "In-Patietns"

    def __str__(self):
        return f"{self.patient.user.fullname} | Room: {self.room_no} | ADM_Date: {self.admission_date}"
    
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Serving', 'Serving'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Billed', 'Billed')
    ]

    patient_user = models.ForeignKey(Patients, on_delete=models.CASCADE) # Jo login hai
    fullname = models.CharField(max_length=100) # Form se aane wala naam
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    contact = models.CharField(max_length=15)
    
    # Relationships with your existing models
    department = models.ForeignKey(Departments, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctors, on_delete=models.CASCADE)
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    
    # Token System fields
    token = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Appointments'
        unique_together = ['doctor', 'appointment_date', 'token']

    def __str__(self):
        return f"Token {self.token} | {self.fullname} | {self.doctor.user.fullname}"
    
class Bills(models.Model):
    BILL_TYPES = [('Out-Patient', 'Out-Patient'), ('In-Patient', 'In-Patient')]
    PAYMENT_STATUS = [('Paid', 'Paid'), ('Unpaid', 'Unpaid'), ('Partial', 'Partial')]

    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='bills')
    patient_type = models.CharField(max_length=20, choices=BILL_TYPES)
    bill_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    admission_date = models.DateField(null=True, blank=True)
    discharge_date = models.DateField(null=True, blank=True)
    staying_days = models.IntegerField(default=0)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS, default='Unpaid')
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'Bills'

    def __str__(self):
        return f"Bill #{self.id} | {self.patient.user.fullname} | {self.patient_type} | {self.grand_total} | {self.payment_status}"

class BillItems(models.Model):
    # 'Bill' ko 'bill' (lowercase) kar diya hai conflict khatam karne ke liye
    bill = models.ForeignKey(Bills, on_delete=models.CASCADE, related_name='items')
    service_name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'Bill_Items'

    def __str__(self):
        return f"{self.service_name} for bill {self.bill.id} [{self.bill.patient.user.fullname}]"
    
class MedicalRecord(models.Model):
    # Aik appointment ka sirf aik hi record ho sakta hai
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_record')
    patient = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='patient_history')
    doctor = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='doctor_prescriptions')
    
    symptoms = models.TextField()
    diagnosis = models.CharField(max_length=255)
    tests = models.TextField(blank=True, null=True)
    medicines_data = models.JSONField(default=list)  # Medicines yahan list mein hongi
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Medical Record"
        verbose_name_plural = "Medical Records"
    
    def __str__(self):
        return f"Record for {self.patient.fullname} - {self.created_at.date()}"