HEF Care Hospital — Hospital Management System (HMS)

A full-featured Hospital Management System built with **Django** and **PostgreSQL**, developed as a Final Year Project (FYP). 
The system manages patients, doctors, appointments, billing, and medical records with role-based access control.

🚀 Features

👨‍💼 Admin
- Dashboard with system overview
- Manage Doctors (Add, Update, View)
- Manage Patients (Add, Update, View)
- Manage Departments
- Manage Appointments
- Generate & Edit Bills
- In-Patient (IPD) Records

👨‍⚕️ Doctor
- Doctor Dashboard
- View & Manage Appointments
- Add/Edit Medical Records
- Manage Schedule
- Edit Profile

🧑‍🦽 Patient
- Patient Dashboard
- Book Appointments
- View Medical Records
- Pay Bills Online (Stripe)
- View Billing History
- Edit Profile
- Submit Feedback

🤖 ML Feature
- Doctor Recommendation System based on symptoms
- Disease prediction using trained ML model (scikit-learn)

🔐 Authentication
- Role-based login (Admin / Doctor / Patient)
- OTP Email Verification
- Forgot Password / Reset Password

⚙️ Installation & Setup

1. Clone the Repository

git clone https://github.com/fatimaabdulhayyi-bit/HMS.git
cd HMS

2. Install Dependencies

pip install -r requirements.txt

3. Setup Environment Variables

Create a .env file in the root directory:

STRIPE_PUBLIC_KEY=your_stripe_public_key_here
STRIPE_SECRET_KEY=your_stripe_secret_key_here
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_16_digit_app_password

5. Setup PostgreSQL Database
Create a database named hospital in PostgreSQL, then update FYP/settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hospital',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

6. Run Migrations
python manage.py migrate

7. Run the Server
python manage.py runserver

Visit: http://127.0.0.1:8000

