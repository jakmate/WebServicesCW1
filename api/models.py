from django.db import models
from django.contrib.auth.models import User

class Professor(models.Model):
    id = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100)

class Module(models.Model):
    code = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100)

class ModuleInstance(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    year = models.IntegerField()
    semester = models.IntegerField()
    professors = models.ManyToManyField(Professor)
    
    class Meta:
        unique_together = ('module', 'year', 'semester')

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    module_instance = models.ForeignKey(ModuleInstance, on_delete=models.CASCADE)
    rating = models.IntegerField()
    
    class Meta:
        unique_together = ('user', 'professor', 'module_instance')