from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends Django's built-in User with a role for RBAC.
    Roles: 'agent' (can only see assigned borrowers) or 'supervisor' (can see all).
    """
    ROLE_CHOICES = [
        ('agent', 'Agent'),
        ('supervisor', 'Supervisor'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


@receiver(post_save, sender='auth.User')
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile with default 'agent' role for every new user."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


class Borrower(models.Model):
    """
    Represents a delinquent borrower account.
    Each borrower is assigned to a specific agent for data isolation.
    """
    name = models.CharField(max_length=255)
    days_past_due = models.IntegerField()
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2)
    prior_payment_behavior = models.CharField(max_length=255)
    hardship_indicator = models.BooleanField(default=False)
    preferred_channel = models.CharField(max_length=50)
    document = models.FileField(
        upload_to='borrower_docs/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        blank=True,
        null=True,
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_borrowers',
        help_text='The agent responsible for this borrower.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.amount_owed} ({self.days_past_due} DPD)"

    class Meta:
        ordering = ['-days_past_due']
