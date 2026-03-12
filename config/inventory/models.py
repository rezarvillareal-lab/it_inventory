from django.db import models

class Inventory(models.Model):
    control_number = models.CharField(max_length=200)
    office_or_hospital = models.CharField(max_length=200)
    user_name = models.CharField(max_length=200)
    computer_name = models.CharField(max_length=200)
    assigned_ip = models.CharField(max_length=200)
    received_by = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    date_received = models.DateField()
    created_at = models.DateField()
    created_by = models.CharField(max_length=100, blank=True, null=True)
    
    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        INACTIVE = "Inactive", "Inactive"
        MAINTENANCE = "Maintenance", "Maintenance"
        CONDEMNED = "Condemned", "Condemned"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
        
    def __str__(self):
        return f"{self.control_number} - {self.user_name}"


class EquipmentComponent(models.Model):
    COMPONENT_CHOICES = [
        # COMPUTER
        ('Processor', 'Processor'),
        ('Motherboard', 'Motherboard'),
        ('Solid State Drive (SSD)', 'Solid State Drive (SSD)'),
        ('Hard Disk Drive (HDD)', 'Hard Disk Drive (HDD)'),
        ('Memory Card 1', 'Memory (RAM) 1'),
        ('Memory Card 2', 'Memory (RAM) 2'),
        ('Video Card', 'Video Card'),
        ('Power Supply Unit', 'Power Supply'),
        ('CPU Case', 'CPU Case'),

        # PERIPHERALS
        ('Monitor', 'Monitor'),
        ('Keyboard', 'Keyboard'),
        ('Mouse', 'Mouse'),
        ('Automatic Voltage Regulator', 'Automatic Voltage Regulator'),
        ('Uninterruptible Power Supply', 'Uninterruptible Power Supply'),
        ('Webcam', 'Webcam'),
        ('Printer', 'Printer'),

        # SOFTWARE
        ('Antivirus Software', 'Antivirus Software'),
        ('MS Office', 'MS Office'),
        ('Operating System', 'Operating System'),
        ('Application Software', 'Application Software'),
    ]

    inventory = models.ForeignKey(
        Inventory,
        related_name='components',
        on_delete=models.CASCADE
    )

    component_name = models.CharField(max_length=100, choices=COMPONENT_CHOICES)

    # ORIGINAL
    original_model = models.CharField(max_length=200, blank=True)
    original_serial = models.CharField(max_length=200, blank=True)

    # REPLACEMENT
    replacement_model = models.CharField(max_length=200, blank=True)
    replacement_serial = models.CharField(max_length=200, blank=True)

    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.component_name} - {self.inventory.control_number}"
