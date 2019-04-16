from rest_framework import serializers

from .models import Authorization, Resource, ResourceCategory
from ..spider.serializers import SpiderSerializer


class AuthorizationSerializer(serializers.ModelSerializer):
    """
    认证序列化
    """

    class Meta:
        model = Authorization
        fields = '__all__'


class ResourceCategorySerializer(serializers.ModelSerializer):
    """
    订阅源类型序列化
    """

    class Meta:
        model = ResourceCategory
        fields = '__all__'


class ResourceSerializer(serializers.ModelSerializer):
    """
    订阅源序列化
    """
    category = ResourceCategorySerializer(read_only=True)
    spider_type = SpiderSerializer(read_only=True)
    auth = AuthorizationSerializer(read_only=True)

    class Meta:
        model = Resource
        fields = '__all__'
