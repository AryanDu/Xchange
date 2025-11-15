from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

# token views
from users.token_views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from users.token_views import MyTokenObtainPairView, EmailTokenView

# signup API view
from users.views import SignupView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/signup/', SignupView.as_view(), name='api-signup'),

    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    
    

    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/email/', EmailTokenView.as_view(), name='token_obtain_email'),

    
    
    
    
]
