from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import Borrower, UserProfile
from .llm_client import LLMWrapperClient

class RBACAndSecurityTests(TestCase):
    def setUp(self):
        # Create users
        self.supervisor = User.objects.create_user(username='supervisor', password='password123')
        UserProfile.objects.get_or_create(user=self.supervisor, defaults={'role': 'supervisor'})
        self.supervisor.profile.role = 'supervisor'
        self.supervisor.profile.save()

        self.agent1 = User.objects.create_user(username='agent1', password='password123')
        UserProfile.objects.get_or_create(user=self.agent1, defaults={'role': 'agent'})
        self.agent1.profile.role = 'agent'
        self.agent1.profile.save()

        self.agent2 = User.objects.create_user(username='agent2', password='password123')
        UserProfile.objects.get_or_create(user=self.agent2, defaults={'role': 'agent'})
        self.agent2.profile.role = 'agent'
        self.agent2.profile.save()

        # Create borrowers
        self.borrower1 = Borrower.objects.create(
            name="Alice",
            days_past_due=10,
            amount_owed=100.0,
            prior_payment_behavior="Good",
            preferred_channel="Email",
            assigned_agent=self.agent1
        )
        self.borrower2 = Borrower.objects.create(
            name="Bob",
            days_past_due=20,
            amount_owed=200.0,
            prior_payment_behavior="Fair",
            preferred_channel="SMS",
            assigned_agent=self.agent2
        )

        self.client = Client()

    def test_agent_can_see_assigned_borrowers(self):
        self.client.login(username='agent1', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice")
        self.assertNotContains(response, "Bob")

    def test_agent_cannot_access_unassigned_borrower_detail(self):
        self.client.login(username='agent1', password='password123')
        response = self.client.get(reverse('borrower_detail', args=[self.borrower2.pk]))
        self.assertEqual(response.status_code, 403)

    def test_supervisor_sees_all_borrowers(self):
        self.client.login(username='supervisor', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice")
        self.assertContains(response, "Bob")


class FileValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

    def test_missing_document_returns_400(self):
        response = self.client.post(reverse('parse_document'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('No document provided', response.json()['error'])

    def test_invalid_extension_returns_400(self):
        file = SimpleUploadedFile("test.txt", b"this is a text file")
        response = self.client.post(reverse('parse_document'), {'document': file})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported file type', response.json()['error'])

    def test_magic_byte_mismatch_returns_400(self):
        # File has .pdf extension but starts with fake magic bytes
        file = SimpleUploadedFile("test.pdf", b"fake magic bytes here")
        response = self.client.post(reverse('parse_document'), {'document': file})
        self.assertEqual(response.status_code, 400)
        self.assertIn('File content does not match its extension', response.json()['error'])


class LLMClientTests(TestCase):
    def test_extract_json_valid(self):
        text = 'Here is the data: {"name": "Test"}'
        result = LLMWrapperClient._extract_json(text)
        self.assertEqual(result, {"name": "Test"})

    def test_extract_json_markdown_fences(self):
        text = '''Some text
        ```json
        {"name": "Markdown Test"}
        ```
        More text
        '''
        result = LLMWrapperClient._extract_json(text)
        self.assertEqual(result, {"name": "Markdown Test"})

    def test_extract_json_invalid(self):
        text = "This is just text without JSON"
        # It should fallback to json.loads, which will fail for non-JSON string
        with self.assertRaises(ValueError):
            LLMWrapperClient._extract_json(text)
