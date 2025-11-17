from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

# token views
from users.token_views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from users.token_views import MyTokenObtainPairView, EmailTokenView
from users.views import SignupView, MeView, UsersListView
# signup API view
from users.views import SignupView 

from users.views import (
    SignupView, MeView, UsersListView,
    SendFriendRequestView, ReceivedFriendRequestsView, SentFriendRequestsView,
    AcceptFriendRequestView, RejectFriendRequestView, CancelFriendRequestView,
    FriendsListView, NotificationsListView, MarkNotificationReadView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/signup/', SignupView.as_view(), name='api-signup'),
    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/email/', EmailTokenView.as_view(), name='token_obtain_email'),
    path('api/me/', MeView.as_view(), name='api-me'),
    path('api/users/', UsersListView.as_view(), name='api-users'),
    path('api/friends/request/', SendFriendRequestView.as_view(), name='friends-send'),
    path('api/friends/requests/received/', ReceivedFriendRequestsView.as_view(), name='friends-received'),
    path('api/friends/requests/sent/', SentFriendRequestsView.as_view(), name='friends-sent'),
    path('api/friends/request/<int:pk>/accept/', AcceptFriendRequestView.as_view(), name='friends-accept'),
    path('api/friends/request/<int:pk>/reject/', RejectFriendRequestView.as_view(), name='friends-reject'),
    path('api/friends/request/<int:pk>/cancel/', CancelFriendRequestView.as_view(), name='friends-cancel'),
    path('api/friends/', FriendsListView.as_view(), name='friends-list'),

# notifications
    path('api/notifications/', NotificationsListView.as_view(), name='notifications-list'),
    path('api/notifications/<int:pk>/mark-read/', MarkNotificationReadView.as_view(), name='notifications-mark-read'),  
]






