import datetime

from django.test import TestCase
from django.urls import reverse

from .models import Inventory


class DashboardViewTests(TestCase):
    def _create_inventory(self, **overrides):
        defaults = {
            "control_number": "CN-0001",
            "office_or_hospital": "Office A",
            "user_name": "User 1",
            "computer_name": "PC-1",
            "assigned_ip": "10.0.0.1",
            "received_by": "Receiver",
            "position": "Staff",
            "date_received": datetime.date(2026, 3, 1),
            "created_at": datetime.date(2026, 3, 19),
            "status": Inventory.Status.ACTIVE,
        }
        defaults.update(overrides)
        return Inventory.objects.create(**defaults)

    def test_dashboard_renders_both_charts_and_context(self):
        self._create_inventory(control_number="CN-1", office_or_hospital="Office A", status=Inventory.Status.ACTIVE)
        self._create_inventory(control_number="CN-2", office_or_hospital="Office A", status=Inventory.Status.ACTIVE)
        self._create_inventory(control_number="CN-3", office_or_hospital="Office B", status=Inventory.Status.MAINTENANCE)
        self._create_inventory(control_number="CN-4", office_or_hospital="Office B", status=Inventory.Status.CONDEMNED)
        self._create_inventory(control_number="CN-5", office_or_hospital="Office C", status=Inventory.Status.DISPOSED)

        response = self.client.get(reverse("inventory:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="officeChart"')
        self.assertContains(response, 'id="statusChart"')

        office_labels = response.context["office_labels"]
        office_counts = response.context["office_counts"]
        status_labels = response.context["status_labels"]
        status_counts = response.context["status_counts"]

        self.assertIsInstance(office_labels, list)
        self.assertIsInstance(office_counts, list)
        self.assertIsInstance(status_labels, list)
        self.assertIsInstance(status_counts, list)

        office_totals = dict(zip(office_labels, office_counts))
        self.assertEqual(office_totals.get("Office A"), 2)
        self.assertEqual(office_totals.get("Office B"), 2)
        self.assertEqual(office_totals.get("Office C"), 1)

        status_totals = dict(zip(status_labels, status_counts))
        self.assertEqual(status_totals.get(Inventory.Status.ACTIVE), 2)
        self.assertEqual(status_totals.get(Inventory.Status.MAINTENANCE), 1)
        self.assertEqual(status_totals.get(Inventory.Status.CONDEMNED), 1)
        self.assertEqual(status_totals.get(Inventory.Status.DISPOSED), 1)
