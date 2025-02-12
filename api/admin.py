from django.contrib import admin
from .models import Professor, Module, ModuleInstance, Rating

admin.site.register(Professor)
admin.site.register(Module)
admin.site.register(ModuleInstance)
admin.site.register(Rating)