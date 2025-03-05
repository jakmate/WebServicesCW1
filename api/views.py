from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.reverse import reverse
from .models import Professor, Module, ModuleInstance, Rating
from .serializers import *

# Endpoint for user registration; allows any user to register
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    # Retrieve registration data from the request
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    # Check for all fields
    if not all([username, email, password]):
        return Response({
            'error': 'Validation Error',
            'code': status.HTTP_400_BAD_REQUEST,
            'details': 'All fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check for duplicates
    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'Conflict',
            'code': status.HTTP_409_CONFLICT,
            'details': 'Username already exists'
        }, status=status.HTTP_409_CONFLICT)

    User.objects.create_user(username=username, email=email, password=password)
    return Response({
        'message': 'User created successfully',
        'links': [
            {
                'description': 'Login with your new account',
                'url': reverse('api_token_auth', request=request),
                'method': 'POST'
            },
            {
                'description': 'Browse API root',
                'url': reverse('api-root', request=request),
                'method': 'GET'
            }
        ]
    }, status=status.HTTP_201_CREATED)

# Viewset for Module model
class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            return Response({
                'error': 'Not Found',
                'code': status.HTTP_404_NOT_FOUND,
                'details': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

# Viewset for ModuleInstance model
class ModuleInstanceViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = ModuleInstance.objects.all()
    serializer_class = ModuleInstanceSerializer

    # Cache this list view for 15 minutes and vary by Cookie and Authorization headers
    @method_decorator(cache_page(60 * 15, key_prefix="modules::list"))
    @method_decorator(vary_on_headers("Cookie", "Authorization"))
    def list(self, request):
        instances = ModuleInstance.objects.all()
        serializer = self.get_serializer(instances, many=True, context={'request': request})
        return Response(serializer.data)

class ProfessorViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer

    # Cache this list view for 15 minutes and vary by Cookie and Authorization headers
    @method_decorator(cache_page(60 * 15, key_prefix="professors::list"))
    @method_decorator(vary_on_headers("Cookie", "Authorization"))
    def list(self, request):
        professors = Professor.objects.all()
        serializer = self.get_serializer(professors, many=True, context={'request': request})
        return Response(serializer.data)

    # Cache this list view for 15 minutes and vary by Cookie and Authorization headers
    # Action to compute the average rating for a professor in a given module
    @method_decorator(cache_page(60 * 15, key_prefix="professor::average"))
    @method_decorator(vary_on_headers("Cookie", "Authorization"))
    @action(detail=True, methods=['get'], url_path='modules/(?P<module_code>[^/.]+)/average', url_name='module-average')
    def average(self, request, pk=None, module_code=None):
        try:
            professor = self.get_object()
            module = Module.objects.get(code=module_code)
        except Module.DoesNotExist:
            return Response({
                'error': 'Not Found',
                'code': status.HTTP_404_NOT_FOUND,
                'details': f'Module {module_code} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate average rating for the professor in given module
        avg_rating = Rating.objects.filter(
            professor=professor,
            module_instance__module=module
        ).aggregate(Avg('rating'))['rating__avg']

        if avg_rating is None:
            return Response({
                'error': 'No Content',
                'code': status.HTTP_204_NO_CONTENT,
                'details': 'No ratings found for this combination'
            }, status=status.HTTP_204_NO_CONTENT)

        return Response({
            "professor_id": professor.id,
            "professor_name": professor.name,
            "module_code": module.code,
            "module_name": module.name,
            "average_rating": round(avg_rating),
            "links": [
                {
                    "rel": "professor",
                    "href": reverse('professor-detail', 
                                kwargs={'pk': professor.id},
                                request=request),
                    "method": "GET"
                }
            ]
        })

# Viewset for Rating model
class RatingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer

    # Return ratings that belong to the logged-in user
    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)

    # Create a new rating
    def perform_create(self, serializer):
        # Retrieve additional data needed for creating a rating
        module_code = self.request.data.get('module_code')
        year = self.request.data.get('year')
        semester = self.request.data.get('semester')
        professor = get_object_or_404(Professor, id=self.request.data.get('professor'))
        module = get_object_or_404(Module, code=module_code)
        module_instance = get_object_or_404(ModuleInstance, module=module, year=year, semester=semester)

        existing_rating = Rating.objects.filter(
            user=self.request.user,
            professor=professor,
            module_instance=module_instance
        ).first()

        # After saving, invalidate relevant caches
        cache_keys = [
            f"professors::{professor.id}",
            f"module::{module.code}",
            "professors::list",
            "modules::list"
        ]

        for key in cache_keys:
            cache.delete(key)

        # Check for existing rating if so update it if not create a new one
        if existing_rating:
            existing_rating.rating = serializer.validated_data.get('rating')
            existing_rating.save()
            serializer.instance = existing_rating
        else:
            serializer.save(
                user=self.request.user,
                module_instance=module_instance,
                professor=professor
            )