from rest_framework import serializers
from django.db.models import Avg
from .models import *
from rest_framework.reverse import reverse

# Serializer for Module model
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

# Serializer for Professor model
class ProfessorSerializer(serializers.ModelSerializer):
    # Field for hypermedia links
    links = serializers.SerializerMethodField()
    # Field for computed average rating
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Professor
        fields = ['id', 'name', 'rating', 'links']

    # Calculate average rating for the professor; return 0 if none found
    def get_rating(self, obj):
        avg = obj.rating_set.aggregate(Avg('rating'))['rating__avg'] or 0
        return round(avg)

    # Build hypermedia links for the professor resource
    def get_links(self, obj):
        return {
            'self': reverse('professor-detail', 
                          kwargs={'pk': obj.id},
                          request=self.context['request']),
            'ratings': reverse('rating-list') + f'?professor={obj.id}',
            'modules': reverse('moduleinstance-list') + f'?professor={obj.id}'
        }

# Serializer for ModuleInstance model
class ModuleInstanceSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    module = ModuleSerializer()
    professors = ProfessorSerializer(many=True)

    class Meta:
        model = ModuleInstance
        fields = ['module', 'year', 'semester', 'professors', 'links']

    # Build hypermedia links for the module instance resource
    def get_links(self, obj):
        return {
            'self': reverse('moduleinstance-detail', 
                          kwargs={'pk': obj.id},
                          request=self.context['request']),
            'module': reverse('module-detail', 
                            kwargs={'pk': obj.module.code},
                            request=self.context['request']),
            'ratings': reverse('rating-list') + f'?module={obj.module.code}'
        }

# Serializer for Rating model
class RatingSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = ['id', 'user', 'professor', 'module_instance', 'rating', 'links']
        # Following fields set server-side
        read_only_fields = ['user', 'module_instance']

    # Build hypermedia links for the rating resource
    def get_links(self, obj):
        return {
            'self': reverse('rating-detail', 
                          kwargs={'pk': obj.id},
                          request=self.context['request']),
            'professor': reverse('professor-detail', 
                                kwargs={'pk': obj.professor.id},
                                request=self.context['request']),
            'module': reverse('module-detail', 
                             kwargs={'pk': obj.module_instance.module.code},
                             request=self.context['request'])
        }