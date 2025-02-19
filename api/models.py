from django.db import models
from django.contrib.auth.models import User

class Professor(models.Model):
    id = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.id}: {self.name}"

class Module(models.Model):
    code = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code}: {self.name}"

class ModuleInstance(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    year = models.IntegerField()
    semester = models.IntegerField()
    professors = models.ManyToManyField(Professor)

    class Meta:
        unique_together = ('module', 'year', 'semester')

    def __str__(self):
        return f"{self.module.code} - {self.year} S{self.semester}"

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    module_instance = models.ForeignKey(ModuleInstance, on_delete=models.CASCADE)
    rating = models.IntegerField()

    class Meta:
        unique_together = ('user', 'professor', 'module_instance')

    def __str__(self):
        username = self.user.username if self.user else "?"
        professor_id = self.professor.id if self.professor else "?"
        module_code = self.module_instance.module.code if self.module_instance and self.module_instance.module else "?"
        year = self.module_instance.year if self.module_instance else "?"
        semester = self.module_instance.semester if self.module_instance else "?"

        return f"Rating {self.rating} for {professor_id} in {module_code} {year} S{semester} by {username}"