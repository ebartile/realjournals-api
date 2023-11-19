from rest_framework import serializers
from .models import LogEntry
    
class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'

class LogEntryDataGridSerializer(serializers.Serializer):
    data = serializers.ListSerializer(child=LogEntrySerializer())
    links = serializers.DictField()
    meta = serializers.DictField()
 