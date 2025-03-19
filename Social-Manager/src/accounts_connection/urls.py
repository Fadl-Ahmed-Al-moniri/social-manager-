from django.urls import path, include
from django.conf.urls import include as clude

from rest_framework.routers import DefaultRouter
from .views import PlatformView , SocialMediaAccountView  
# from .views import  FacebookLogin , get_facebook_access_token
# from allauth.socialaccount import views as socialaccount_views



router = DefaultRouter()

router.register(r'platform', PlatformView, basename='platform')
router.register(r'social-manager', SocialMediaAccountView, basename='social-manager')

urlpatterns = [
    path('', include(router.urls)),
    # path('rest-auth/facebook/', FacebookLogin.as_view(), name='fb_login'),
    # path('signup/', socialaccount_views.signup, name='socialaccount_signup'),
    # path('get_facebook_access_token', get_facebook_access_token, name='get_facebook_access_token'),

    # path('rest-auth/registration/', include('rest_auth.registration.urls')),
    # path('rest-auth/facebook/', FacebookLogin.as_view(), name='fb_login'),


]

