from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer
from django.db import models

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
    
    
# append to backend/users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db import IntegrityError, transaction
from django.conf import settings
from .models import FriendRequest, Friendship, Notification
from .serializers import FriendRequestSerializer, FriendshipSerializer, NotificationSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Helper: create canonical friendship tuple (small_id, big_id)
def _make_friendship(user_a, user_b):
    a, b = (user_a, user_b) if user_a.id < user_b.id else (user_b, user_a)
    return a, b

class SendFriendRequestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        to_user_id = request.data.get('to_user')
        if not to_user_id:
            return Response({"detail":"to_user required"}, status=status.HTTP_400_BAD_REQUEST)
        if int(to_user_id) == request.user.id:
            return Response({"detail":"cannot send request to yourself"}, status=status.HTTP_400_BAD_REQUEST)
        to_user = get_object_or_404(User, id=to_user_id)

        # if already friends -> error
        a, b = _make_friendship(request.user, to_user)
        if Friendship.objects.filter(user1=a, user2=b).exists():
            return Response({"detail":"already friends"}, status=status.HTTP_400_BAD_REQUEST)

        # if reverse pending request exists -> accept it automatically
        reverse = FriendRequest.objects.filter(from_user=to_user, to_user=request.user, status=FriendRequest.STATUS_PENDING).first()
        if reverse:
            # accept reverse request
            with transaction.atomic():
                reverse.status = FriendRequest.STATUS_ACCEPTED
                reverse.save()
                u1, u2 = _make_friendship(request.user, to_user)
                Friendship.objects.get_or_create(user1=u1, user2=u2)
                # create notifications
                Notification.objects.create(user=to_user, actor_user=request.user, type=Notification.NOTIF_FRIEND_ACCEPT, text=f"{request.user.get_username()} accepted your request")
                Notification.objects.create(user=request.user, actor_user=to_user, type=Notification.NOTIF_FRIEND_ACCEPT, text=f"You are now friends with {to_user.get_username()}")
            return Response({"detail":"mutual request accepted"}, status=status.HTTP_200_OK)

        # normal create pending request (prevent duplicates)
        try:
            fr, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
            if not created:
                if fr.status == FriendRequest.STATUS_PENDING:
                    return Response({"detail":"request already pending"}, status=status.HTTP_400_BAD_REQUEST)
                # if previously rejected/cancelled, recreate
                fr.status = FriendRequest.STATUS_PENDING
                fr.save()
            # create notification for receiver
            Notification.objects.create(user=to_user, actor_user=request.user, type=Notification.NOTIF_FRIEND_REQUEST, text=f"{request.user.get_username()} sent you a connection request", data={"request_id": fr.id})
        except IntegrityError:
            return Response({"detail":"duplicate request"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(FriendRequestSerializer(fr).data, status=status.HTTP_201_CREATED)


class ReceivedFriendRequestsView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user).order_by('-created_at')


class SentFriendRequestsView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(from_user=self.request.user).order_by('-created_at')


class AcceptFriendRequestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        fr = get_object_or_404(FriendRequest, id=pk)
        if fr.to_user.id != request.user.id:
            return Response({"detail":"not allowed"}, status=status.HTTP_403_FORBIDDEN)
        if fr.status != FriendRequest.STATUS_PENDING:
            return Response({"detail":"request not pending"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            fr.status = FriendRequest.STATUS_ACCEPTED
            fr.save()
            u1, u2 = _make_friendship(fr.from_user, fr.to_user)
            Friendship.objects.get_or_create(user1=u1, user2=u2)
            # notifications
            Notification.objects.create(user=fr.from_user, actor_user=fr.to_user, type=Notification.NOTIF_FRIEND_ACCEPT, text=f"{fr.to_user.get_username()} accepted your request", data={"request_id": fr.id})
            Notification.objects.create(user=fr.to_user, actor_user=fr.from_user, type=Notification.NOTIF_FRIEND_ACCEPT, text=f"You are now friends with {fr.from_user.get_username()}", data={"request_id": fr.id})
        return Response({"detail":"accepted"}, status=status.HTTP_200_OK)


class RejectFriendRequestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        fr = get_object_or_404(FriendRequest, id=pk)
        if fr.to_user.id != request.user.id:
            return Response({"detail":"not allowed"}, status=status.HTTP_403_FORBIDDEN)
        if fr.status != FriendRequest.STATUS_PENDING:
            return Response({"detail":"request not pending"}, status=status.HTTP_400_BAD_REQUEST)
        fr.status = FriendRequest.STATUS_REJECTED
        fr.save()
        Notification.objects.create(user=fr.from_user, actor_user=fr.to_user, type=Notification.NOTIF_SYSTEM, text=f"{fr.to_user.get_username()} rejected your connection request", data={"request_id": fr.id})
        return Response({"detail":"rejected"}, status=status.HTTP_200_OK)


class CancelFriendRequestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, pk):
        fr = get_object_or_404(FriendRequest, id=pk)
        if fr.from_user.id != request.user.id:
            return Response({"detail":"not allowed"}, status=status.HTTP_403_FORBIDDEN)
        if fr.status != FriendRequest.STATUS_PENDING:
            return Response({"detail":"cannot cancel"}, status=status.HTTP_400_BAD_REQUEST)
        fr.status = FriendRequest.STATUS_CANCELLED
        fr.save()
        return Response({"detail":"cancelled"}, status=status.HTTP_200_OK)


class FriendsListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FriendshipSerializer

    def get_queryset(self):
        user = self.request.user
        # friendships where user is user1 or user2
        return Friendship.objects.filter(models.Q(user1=user) | models.Q(user2=user)).order_by('-created_at')


# Notifications
class NotificationsListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')[:50]


class MarkNotificationReadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        notif = get_object_or_404(Notification, id=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return Response({"detail":"marked"}, status=status.HTTP_200_OK)






