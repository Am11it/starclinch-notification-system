import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile


class Command(BaseCommand):
    help = "Create the admin user from ADMIN_EMAIL / ADMIN_PASSWORD (safe to run many times)."

    def handle(self, *args, **options):
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        if not email or not password:
            self.stdout.write("ADMIN_EMAIL / ADMIN_PASSWORD not set, skipping")
            return

        user, created = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": "Admin"})
        user.is_staff = True
        user.is_superuser = True
        if created:
            user.set_password(password)
        user.save()
        Profile.objects.get_or_create(user=user)
        self.stdout.write(f"Admin {'created' if created else 'already exists'}: {email}")
