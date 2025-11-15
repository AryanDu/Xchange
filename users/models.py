from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Use JSONField from django (works on modern Django with SQLite)
try:
    # Django 3.1+ exposes JSONField in core
    from django.db.models import JSONField
except Exception:
    # fallback for very old Django (unlikely); store as TextField
    JSONField = models.TextField

class User(AbstractUser):
    full_name = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    age = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(120)]
    )
    avatar_url = models.URLField(blank=True)
    skills = JSONField(default=list, blank=True)
    languages = JSONField(default=list, blank=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.full_name or self.username
