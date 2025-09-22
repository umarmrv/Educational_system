from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from Education.views import UserViewSet,GroupViewSet 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
# from .views import GroupViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register(r'groups', GroupViewSet, basename='group')


urlpatterns = [

      # Документация (по желанию, но полезно)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),


    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/admin/')),

        # Наш API
    path("api/", include(router.urls)),

    # JWT (получение токена/обновление)
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
