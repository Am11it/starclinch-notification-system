from django.core.management.base import BaseCommand

from notifications.services import check_inactive_users


class Command(BaseCommand):
    help = "Fire 'Not logged in for 1 day / 1 week' triggers. Run it from a cron job."

    def handle(self, *args, **options):
        self.stdout.write(f"Notified {check_inactive_users()} user(s)")
