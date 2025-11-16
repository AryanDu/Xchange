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
    
    
    
    

# backend/users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

from .serializers import UserSerializer

User = get_user_model()

# -------------------------
# GET /api/me/  -> current user
# -------------------------
class MeView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

# -------------------------
# GET /api/users/  -> users list + simple filters
# query params supported:
#   ?search=python         (search in skills or full_name)
#   ?age=18-25 or lt18 or 35+
#   ?skills=Python,ML      (comma-separated)
#   ?lang=Hindi
# -------------------------
class UsersListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    pagination_class = None  # remove or set a DRF paginator if desired

    def get_queryset(self):
        qs = User.objects.filter(is_active=True).order_by('-id')  # newest first

        # get raw query params
        search = self.request.query_params.get('search', '').strip()
        age = self.request.query_params.get('age', '').strip()
        skills_q = self.request.query_params.get('skills', '').strip()
        lang = self.request.query_params.get('lang', '').strip()

        # filter by age range
        if age:
            if age == 'lt18':
                qs = qs.filter(age__lt=18)
            elif age == '35+':
                qs = qs.filter(age__gte=35)
            elif '-' in age:
                parts = age.split('-', 1)
                try:
                    a1 = int(parts[0]); a2 = int(parts[1])
                    qs = qs.filter(age__gte=a1, age__lte=a2)
                except ValueError:
                    pass

        # For skills/lang/search — SQLite may not support JSON lookups consistently,
        # so we filter in Python for safety (works fine for small prototype / 10 users).
        users = list(qs)

        def matches(u):
            # search in full_name or skills
            if search:
                s = search.lower()
                name_ok = (u.full_name or u.username or '').lower().find(s) != -1
                skills_ok = False
                try:
                    for sk in (u.skills or []):
                        if s in str(sk).lower():
                            skills_ok = True; break
                except Exception:
                    skills_ok = False
                if not (name_ok or skills_ok):
                    return False

            if skills_q:
                wanted = [x.strip().lower() for x in skills_q.split(',') if x.strip()]
                user_skills = [str(x).lower() for x in (u.skills or [])]
                # require that user has at least one of the wanted skills
                if not any(w in ' '.join(user_skills) for w in wanted):
                    return False

            if lang:
                user_langs = [str(x).lower() for x in (u.languages or [])]
                if lang.lower() not in user_langs:
                    return False

            return True

        filtered = [u for u in users if matches(u)]

        # If no filters provided, emulate "random / instagram" feel by shuffling
        if not (search or age or skills_q or lang):
            import random
            random.shuffle(filtered)

        return filtered





