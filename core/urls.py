from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_transaction, name='create_transaction'),
    path('hey', views.summarize_bank_statement, name='summarize-bank-statement'),
]
