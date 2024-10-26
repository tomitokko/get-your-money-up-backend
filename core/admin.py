from django.contrib import admin
from .models import Transaction, CategorisedTransaction

# Register your models here.
admin.site.register(Transaction)
admin.site.register(CategorisedTransaction)