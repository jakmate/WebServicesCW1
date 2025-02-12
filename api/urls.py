from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a new router instance
router = DefaultRouter()

# Register viewsets
router.register(r'module-instances', views.ModuleInstanceViewSet)
router.register(r'professors', views.ProfessorViewSet)
router.register(r'ratings', views.RatingViewSet, basename='rating')
router.register(r'modules', views.ModuleViewSet)

urlpatterns = [
    # Include all routes generated by the router
    path('', include(router.urls)),
]