from django.contrib import admin
from .models import Professor, Module, ModuleInstance, Rating

# Register models with the admin site
admin.site.register(Professor)
admin.site.register(Module)
admin.site.register(ModuleInstance)
admin.site.register(Rating)