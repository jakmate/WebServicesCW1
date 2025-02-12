from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Professor, Module, ModuleInstance, Rating
from .serializers import *

@api_view(['POST'])
@permission_classes([AllowAny]) 
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not all([username, email, password]):
        return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, email=email, password=password)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

class ModuleInstanceViewSet(viewsets.ModelViewSet):
    queryset = ModuleInstance.objects.all()
    serializer_class = ModuleInstanceSerializer

    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_headers("Cookie", "Authorization"))
    def list(self, request):
        instances = ModuleInstance.objects.all()
        serializer = self.get_serializer(instances, many=True, context={'request': request})
        return Response(serializer.data)

class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer

    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_headers("Cookie", "Authorization"))
    def list(self, request):
        professors = Professor.objects.all()
        serializer = self.get_serializer(professors, many=True, context={'request': request})
        return Response(serializer.data)


    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_headers("Cookie", "Authorization"))
    @action(detail=True, methods=['get'], url_path='modules/(?P<module_code>[^/.]+)/average')
    def average(self, request, pk=None, module_code=None):
        professor = self.get_object()
        module = Module.objects.filter(code=module_code).first()
        
        if not module:
            return Response({"error": "Module not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate average rating for the professor in this module
        avg_rating = Rating.objects.filter(
            professor=professor,
            module_instance__module=module
        ).aggregate(Avg('rating'))['rating__avg']
        
        if avg_rating is None:
            return Response({"error": "No ratings found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "professor_id": professor.id,
            "professor_name": professor.name,
            "module_code": module.code,
            "module_name": module.name,
            "average_rating": round(avg_rating)
        })

class RatingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
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