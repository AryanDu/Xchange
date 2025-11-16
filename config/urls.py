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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/signup/', SignupView.as_view(), name='api-signup'),

    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    
    

    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/email/', EmailTokenView.as_view(), name='token_obtain_email'),
    

# ...
    path('api/me/', MeView.as_view(), name='api-me'),
    path('api/users/', UsersListView.as_view(), name='api-users'),

    


    
    
    
    
]
