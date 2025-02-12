from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'module-instances', views.ModuleInstanceViewSet)
router.register(r'professors', views.ProfessorViewSet)
router.register(r'ratings', views.RatingViewSet, basename='rating')
router.register(r'modules', views.ModuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]