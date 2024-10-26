from rest_framework import serializers
from .models import Transaction, CategorisedTransaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
