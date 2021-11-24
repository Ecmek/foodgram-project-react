from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ( 'id', 'email', 'username', 'first_name', 'last_name',)

class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ( 'id', 'email', 'username', 'first_name', 'last_name', 'password',)


class UserPasswordSerializer(serializers.Serializer):

    new_password = serializers.CharField(label=_('New password'))
    current_password = serializers.CharField(label=_('Current password'))

    def validate(self, data):
        user = self.context['request'].user
        current_password = data.get('current_password')

        if not authenticate(username=user.email, password=current_password):
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        password = make_password(validated_data.get('new_password'))
        user.password = password
        user.save()
        return validated_data


class TokenSerializer(AuthTokenSerializer):
    email = serializers.CharField(
        label=_('Email'),
        write_only=True
    )
    password = serializers.CharField(
        label=_('Password'),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_('Token'),
        read_only=True
    )

    def validate(self, attrs):
        username = attrs.get('email')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
