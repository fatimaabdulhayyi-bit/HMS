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
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin