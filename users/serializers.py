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

    
    
    
    
    
    
    
