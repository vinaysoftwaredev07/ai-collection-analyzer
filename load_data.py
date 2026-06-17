"""
Load synthetic borrower data with agent assignments.
Run after seed_users to ensure agent1 and agent2 exist.

Usage:
    python load_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collections_optimizer.settings')
django.setup()

from django.contrib.auth.models import User
from strategy.models import Borrower

# Clear existing data
Borrower.objects.all().delete()
print("Cleared existing borrower data.")

# Fetch seeded agents
try:
    agent1 = User.objects.get(username='agent1')
    agent2 = User.objects.get(username='agent2')
except User.DoesNotExist:
    print("ERROR: Run 'python manage.py seed_users' first to create demo users.")
    exit(1)

borrowers = [
    # Assigned to agent1
    {
        "name": "Alice Smith",
        "days_past_due": 15,
        "amount_owed": 250.00,
        "prior_payment_behavior": "Usually pays on time, first-time delinquency",
        "hardship_indicator": False,
        "preferred_channel": "Email",
        "assigned_agent": agent1,
    },
    {
        "name": "Charlie Davis",
        "days_past_due": 45,
        "amount_owed": 800.00,
        "prior_payment_behavior": "Good payer, recently lost job",
        "hardship_indicator": True,
        "preferred_channel": "Phone Call",
        "assigned_agent": agent1,
    },
    {
        "name": "Eva Martinez",
        "days_past_due": 30,
        "amount_owed": 1500.00,
        "prior_payment_behavior": "Occasional late payments, usually within grace period",
        "hardship_indicator": False,
        "preferred_channel": "SMS",
        "assigned_agent": agent1,
    },
    # Assigned to agent2
    {
        "name": "Bob Johnson",
        "days_past_due": 95,
        "amount_owed": 1200.00,
        "prior_payment_behavior": "Habitually late, missed last 3 payments",
        "hardship_indicator": False,
        "preferred_channel": "SMS",
        "assigned_agent": agent2,
    },
    {
        "name": "Diana Evans",
        "days_past_due": 120,
        "amount_owed": 3500.00,
        "prior_payment_behavior": "Unresponsive to all previous outreach attempts",
        "hardship_indicator": False,
        "preferred_channel": "Email",
        "assigned_agent": agent2,
    },
    {
        "name": "Frank Wilson",
        "days_past_due": 60,
        "amount_owed": 2200.00,
        "prior_payment_behavior": "Made partial payments last quarter, medical emergency",
        "hardship_indicator": True,
        "preferred_channel": "Phone Call",
        "assigned_agent": agent2,
    },
]

for b in borrowers:
    Borrower.objects.create(**b)

print(f"Successfully loaded {len(borrowers)} synthetic borrowers.")
print(f"  agent1 ({agent1.get_full_name()}): {Borrower.objects.filter(assigned_agent=agent1).count()} borrowers")
print(f"  agent2 ({agent2.get_full_name()}): {Borrower.objects.filter(assigned_agent=agent2).count()} borrowers")
