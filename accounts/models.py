from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('member', 'Membre'),
        ('guest', 'Invité'),
    )

    first_name = models.CharField(max_length=150)
    last_name  = models.CharField(max_length=150)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    photo      = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio        = models.TextField(blank=True)
    birth_date = models.DateField(default='2000-01-01')
    family     = models.ForeignKey(
        'Family',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='members'
    )


import uuid

class Family(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    created_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL,
        null=True, related_name='created_families'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4()).upper()[:8]  # ex: A3F9B2C1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class JoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending',  'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Refusée'),
    )
    user     = models.ForeignKey('User',   on_delete=models.CASCADE, related_name='join_requests')
    family   = models.ForeignKey(Family,   on_delete=models.CASCADE, related_name='join_requests')
    relation = models.CharField(max_length=100, blank=True, default='')
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} → {self.family} ({self.status})"