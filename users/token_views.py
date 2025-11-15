# backend/users/token_views.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

# Keep existing token view for username-based auth (optional)
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name'] = getattr(user, 'full_name', '')
        token['email'] = getattr(user, 'email', '')
        return token

    def validate(self, attrs):
        # resolve email->username if email provided
        email = attrs.get('email')
        if email and 'username' not in attrs:
            try:
                user = User.objects.get(email=email)
                attrs['username'] = user.get_username()
            except User.DoesNotExist:
                pass
        data = super().validate(attrs)
        user = self.user
        data.update({
            "id": user.id,
            "full_name": getattr(user, "full_name", ""),
            "email": getattr(user, "email", ""),
        })
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# --- NEW: simple email login view that returns tokens directly ---
class EmailTokenView(APIView):
    """
    POST { "email": "...", "password": "..." }
    Returns: { access, refresh, id, email, full_name }
    """
    authentication_classes = []  # no auth required
    permission_classes = []      # open endpoint

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return Response({"detail":"email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail":"No active account found with the given credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"detail":"No active account found with the given credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"detail":"User account is disabled."}, status=status.HTTP_403_FORBIDDEN)

        # create tokens
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            "access": access,
            "refresh": refresh_token,
            "id": user.id,
            "email": user.email,
            "full_name": getattr(user, "full_name", "")
        }, status=status.HTTP_200_OK)
