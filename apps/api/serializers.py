# apps/api/serializers.py
from rest_framework import serializers
from apps.users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optimize queries by selecting related profile when needed
        if hasattr(self, 'context') and 'view' in self.context:
            view = self.context['view']
            if hasattr(view, 'get_queryset'):
                view.queryset = view.get_queryset().select_related('profile')