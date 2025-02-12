from rest_framework import serializers
from django.db.models import Avg
from .models import *

'''class ProfessorSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    
    def get_rating(self, obj):
        avg = obj.rating_set.aggregate(Avg('rating'))['rating__avg'] or 0
        return round(avg)
    
    class Meta:
        model = Professor
        fields = '__all__'

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class ModuleInstanceSerializer(serializers.ModelSerializer):
    module = ModuleSerializer()
    professors = ProfessorSerializer(many=True)
    
    class Meta:
        model = ModuleInstance
        fields = '__all__'

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'user', 'professor', 'module_instance', 'rating']
        read_only_fields = ['user', 'module_instance']'''

from rest_framework.reverse import reverse

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class ProfessorSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Professor
        fields = ['id', 'name', 'rating', 'links']

    def get_rating(self, obj):
        avg = obj.rating_set.aggregate(Avg('rating'))['rating__avg'] or 0
        return round(avg)

    def get_links(self, obj):
        return {
            'self': reverse('professor-detail', 
                          kwargs={'pk': obj.id},
                          request=self.context['request']),
            'ratings': reverse('rating-list') + f'?professor={obj.id}',
            'modules': reverse('moduleinstance-list') + f'?professor={obj.id}'
        }

class ModuleInstanceSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()
    module = ModuleSerializer()
    professors = ProfessorSerializer(many=True)

    class Meta:
        model = ModuleInstance
        fields = ['module', 'year', 'semester', 'professors', 'links']

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

class RatingSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = ['id', 'user', 'professor', 'module_instance', 'rating', 'links']
        read_only_fields = ['user', 'module_instance']

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