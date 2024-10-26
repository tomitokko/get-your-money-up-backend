from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_transaction, name='create_transaction'),
]
