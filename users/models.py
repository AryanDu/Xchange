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

# append to backend/users/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class FriendRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        indexes = [
            models.Index(fields=['to_user', 'status']),
            models.Index(fields=['from_user', 'status']),
        ]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"


class Friendship(models.Model):
    # canonical ordering: always store user_small_id first for uniqueness
    user1 = models.ForeignKey(User, related_name='friendships1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='friendships2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user1', 'user2'),)
        indexes = [models.Index(fields=['user1']), models.Index(fields=['user2'])]

    def __str__(self):
        return f"Friendship {self.user1} <-> {self.user2}"


class Notification(models.Model):
    """
    Simple notification model for in-app notifications.
    type: friend_request, friend_accept, message, system...
    data: small JSON/text payload (e.g. {'request_id': 5})
    """
    NOTIF_FRIEND_REQUEST = 'friend_request'
    NOTIF_FRIEND_ACCEPT = 'friend_accept'
    NOTIF_MESSAGE = 'message'
    NOTIF_SYSTEM = 'system'

    NOTIF_TYPES = [
        (NOTIF_FRIEND_REQUEST, 'Friend request'),
        (NOTIF_FRIEND_ACCEPT, 'Friend accept'),
        (NOTIF_MESSAGE, 'Message'),
        (NOTIF_SYSTEM, 'System'),
    ]

    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    actor_user = models.ForeignKey(User, null=True, blank=True, related_name='notifications_by', on_delete=models.SET_NULL)
    type = models.CharField(max_length=32, choices=NOTIF_TYPES)
    text = models.CharField(max_length=255)
    data = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'is_read']), models.Index(fields=['user', 'created_at'])]

    def __str__(self):
        return f"Notif {self.type} -> {self.user} ({'read' if self.is_read else 'new'})"
