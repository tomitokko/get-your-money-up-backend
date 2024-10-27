from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_transaction, name='create_transaction'),
    # path('hey', views.summarize_bank_statement, name='summarize-bank-statement'),
    path('summarize/<str:bank_statement_uid>/', views.summarize_bank_statement, name='summarize_bank_statement'),
    path('savings/<str:bank_statement_uid>/', views.savings_info, name='savings_info'),

]
