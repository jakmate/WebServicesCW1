from rest_framework import serializers
from django.db.models import Avg
from .models import *
from rest_framework.reverse import reverse
from django.contrib.auth.models import User

# Serializer for Module model
class ModuleSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = '__all__'

    def get_links(self, obj):
        request = self.context['request']
        return {
            'self': {
                'url': reverse('module-detail', kwargs={'pk': obj.code}, request=request),
                'method': 'GET'
            },
            'instances': {
                'url': reverse('moduleinstance-list') + f'?module={obj.code}',
                'method': 'GET'
            },
            'ratings': {
                'url': reverse('rating-list') + f'?module={obj.code}',
                'method': 'GET'
            }
        }

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
            'self': {
                'url': reverse('professor-detail', 
                          kwargs={'pk': obj.id},
                          request=self.context['request']),
                'method': 'GET'
            },
            'ratings': {
                'url': reverse('rating-list') + f'?professor={obj.id}',
                'method': 'GET'
            },
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
        request = self.context['request']
        links = {
            'self': {
                'url': reverse('moduleinstance-detail', 
                              kwargs={'pk': obj.id}, 
                              request=request),
                'method': 'GET'
            }
        }
        
        # Add average rating links for each professor in this module instance
        for professor in obj.professors.all():
            links[f'average_{professor.id}'] = {
                'url': reverse('professor-module-average',
                              kwargs={
                                  'pk': professor.id,
                                  'module_code': obj.module.code
                              },
                              request=request),
                'method': 'GET',
                'description': f'Average rating for {professor.name} in this module'
            }
        
        return links

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
        request = self.context['request']
        return {
            'self': {
                'url': reverse('rating-detail', kwargs={'pk': obj.id}, request=request),
                'method': 'GET'
            },
            'professor': {
                'url': reverse('professor-detail', kwargs={'pk': obj.professor.id}, request=request),
                'method': 'GET'
            },
            'module_instance': {
                'url': reverse('moduleinstance-detail', kwargs={'pk': obj.module_instance.id}, request=request),
                'method': 'GET'
            }
        }
    
class UserSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'email', 'links']
        read_only_fields = ['username', 'email']  # Prevent accidental updates

    def get_links(self, obj):
        request = self.context['request']
        return {
            'ratings': {
                'url': reverse('rating-list') + f'?user={obj.id}',
                'method': 'GET'
            }
        }