from django.db import models
import uuid

# Create your models here.

class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    bank_statement_uid = models.UUIDField()
    date = models.DateField()
    time = models.TimeField()
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    description = models.TextField(blank=True, null=True)
    money_out = models.DecimalField(max_digits=1000, decimal_places=2, blank=True, null=True)
    money_in = models.DecimalField(max_digits=1000, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.category} - {self.amount} {self.currency}"

class CategorisedTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    bank_statement_uid = models.UUIDField()
    category = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    money_out = models.DecimalField(max_digits=1000, decimal_places=2, blank=True, null=True)
    money_in = models.DecimalField(max_digits=1000, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=10)

