"""
Management command to seed demo users for the prototype.
Creates supervisor and agent accounts with UserProfile roles.
Idempotent — safe to run multiple times.
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from strategy.models import UserProfile


DEMO_USERS = [
    {
        'username': 'supervisor',
        'password': 'supervisor123',
        'email': 'supervisor@biz2x.com',
        'first_name': 'Sarah',
        'last_name': 'Manager',
        'role': 'supervisor',
        'is_staff': True,
    },
    {
        'username': 'agent1',
        'password': 'agent123',
        'email': 'agent1@biz2x.com',
        'first_name': 'Alice',
        'last_name': 'Agent',
        'role': 'agent',
        'is_staff': False,
    },
    {
        'username': 'agent2',
        'password': 'agent123',
        'email': 'agent2@biz2x.com',
        'first_name': 'Bob',
        'last_name': 'Agent',
        'role': 'agent',
        'is_staff': False,
    },
]


class Command(BaseCommand):
    help = 'Seed demo users with roles (supervisor, agent1, agent2)'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stderr.write(self.style.WARNING(
                "WARNING: Seeding demo users in non-DEBUG mode! "
                "These accounts use weak passwords. Do NOT use in production."
            ))

        for entry in DEMO_USERS:
            # Work on a copy so the module-level list is never mutated
            user_data = {**entry}
            role = user_data.pop('role')
            password = user_data.pop('password')

            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': user_data['is_staff'],
                },
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"  Created user: {user.username} (password: {password})"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"  User already exists: {user.username}"
                ))

            # Create or update profile (signal may have already created it)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            self.stdout.write(f"    Role set to: {role}")

        self.stdout.write(self.style.SUCCESS("\nDemo users seeded successfully!"))
        self.stdout.write("\nLogin credentials:")
        self.stdout.write("  supervisor / supervisor123  (sees all borrowers)")
        self.stdout.write("  agent1     / agent123       (sees only assigned borrowers)")
        self.stdout.write("  agent2     / agent123       (sees only assigned borrowers)")
