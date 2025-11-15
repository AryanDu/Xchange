from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer

class SignupView(APIView):
    permission_classes = []  # allow unauthenticated

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # return minimal public info
            data = {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# backend/users/token_views.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework import serializers

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    # allow login with email instead of username
    username_field = User.EMAIL_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # add custom claims if you want:
        token['full_name'] = user.full_name
        token['email'] = user.email
        return token

    def validate(self, attrs):
        # We want to accept "email" + "password"
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }
        # find user by email
        try:
            user = User.objects.get(email=credentials['email'])
            username = user.get_username()
        except User.DoesNotExist:
            username = None

        # set username in attrs so TokenObtainPairSerializer can run authenticate
        if username:
            attrs['username'] = username

        data = super().validate(attrs)
        # Optionally, include user info in response
        data.update({
            "id": self.user.id,
            "full_name": self.user.full_name,
            "email": self.user.email,
        })
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer




