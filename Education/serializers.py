from django.contrib.auth import get_user_model
from rest_framework import serializers

from Education.models import Role  # enum ролей

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Один сериализатор и на чтение, и на запись.
    - Если передан password — хэшируем и сохраняем.
    - Если password не передан при создании — сгенерируем случайный.
    """
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = (
            "id", "username", "password", "full_name", "email", "phone",
            "role", "is_active", "date_joined",
        )
        read_only_fields = ("id", "date_joined")

    def create(self, validated_data):
        pwd = validated_data.pop("password", None)
        user = User(**validated_data)
        if pwd:
            user.set_password(pwd)
        else:
            user.set_password(User.objects.make_random_password())
        user.save()
        return user

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance
