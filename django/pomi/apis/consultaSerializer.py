from rest_framework import serializers

class whatsAppIn(serializers.Serializer):
    sender = serializers.CharField()
    from_number = serializers.CharField()
    text = serializers.CharField()