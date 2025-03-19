
from rest_framework import serializers

class ListToStringField(serializers.Field):
    def to_representation(self, value):
        if value:
            return value.split(",")
        return []

    def to_internal_value(self, data):
        if isinstance(data, list):
            return ",".join(data)
        raise serializers.ValidationError("Expected a list of strings.")
    
