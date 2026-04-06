from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            # 1. Pehle check karein ke user login hai ya nahi
            if not request.user.is_authenticated:
                return redirect('login')
            
            # 2. Check karein ke user ka role allowed list mein maujood hai?
            # Humne 'or request.user.is_superuser' yahan se nikal diya hai
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                # Agar role match nahi karta
                messages.warning(request, "You do not have permission to access this page.")
                
                # Role ke mutabiq sahi dashboard par bhejein taake baar baar login na karna paray
                if request.user.role == 'doctor':
                    return redirect('doctor_dashboard')
                elif request.user.role == 'patient':
                    return redirect('patient_dashboard')
                elif request.user.role == 'admin':
                    return redirect('admin_dashboard')
                
                return redirect('login') 
        return wrap
    return decorator