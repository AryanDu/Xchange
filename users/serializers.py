from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

User = get_user_model() 

def word_count(text):
    # count words robustly
    words = [w for w in text.strip().split() if w]
    return len(words)

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    languages = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = User
        fields = ('id','full_name','email','password','bio','age','avatar_url','skills','languages')

    def validate_full_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_bio(self, value):
        # Enforce 100 - 200 words
        wc = word_count(value)
        if wc < 100:
            raise serializers.ValidationError(f"Bio too short ({wc} words). Minimum 100 words required.")
        if wc > 200:
            raise serializers.ValidationError(f"Bio too long ({wc} words). Maximum 200 words allowed.")
        return value

    def validate_age(self, value):
        if value is None:
            raise serializers.ValidationError("Age is required.")
        if value < 1 or value > 120:
            raise serializers.ValidationError("Enter a valid age.")
        return value

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        # ensure username exists since AbstractUser requires it; we'll set username = email
        email = validated_data.get('email')
        validated_data['username'] = email.split('@')[0]  # simple username default
        user = User(**validated_data)
        user.password = make_password(password)
        user.save()
        return user
    
# backend/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    # If skills/languages are JSONField/list, DRF handles them.
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "email",
            "age",
            "avatar_url",
            "bio",
            "skills",
            "languages",
            "is_active",
        )
        read_only_fields = ("id", "username", "email", "is_active")


# append to backend/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FriendRequest, Friendship, Notification

User = get_user_model()

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.SerializerMethodField()
    to_user = serializers.SerializerMethodField()

    class Meta:
        model = FriendRequest
        fields = ('id','from_user','to_user','status','created_at')

    def get_from_user(self, obj):
        return {"id": obj.from_user.id, "full_name": getattr(obj.from_user, 'full_name', ''), "avatar_url": getattr(obj.from_user,'avatar_url','')}

    def get_to_user(self, obj):
        return {"id": obj.to_user.id, "full_name": getattr(obj.to_user, 'full_name', ''), "avatar_url": getattr(obj.to_user,'avatar_url','')}


class FriendshipSerializer(serializers.ModelSerializer):
    friend = serializers.SerializerMethodField()
    class Meta:
        model = Friendship
        fields = ("id","friend","created_at")
    def get_friend(self, obj):
        request_user = self.context.get('request').user
        other = obj.user2 if obj.user1.id == request_user.id else obj.user1
        return {"id": other.id, "full_name": getattr(other,'full_name',''), "avatar_url": getattr(other,'avatar_url','')}


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    class Meta:
        model = Notification
        fields = ("id","type","text","data","is_read","actor","created_at")

    def get_actor(self, obj):
        if not obj.actor_user:
            return None
        return {"id": obj.actor_user.id, "full_name": getattr(obj.actor_user,'full_name',''), "avatar_url": getattr(obj.actor_user,'avatar_url','')}

    
    
    
    
    
    
    
