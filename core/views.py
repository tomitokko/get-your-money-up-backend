from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Transaction, CategorisedTransaction
from .serializers import TransactionSerializer
import pandas as pd
import os
from django.conf import settings
from django.http import JsonResponse


@api_view(['POST'])
def create_transaction(request):
    serializer = TransactionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# summarize bank statements based on categories
def summarize_bank_statement(request, bank_statement_uid):
    transactions = Transaction.objects.filter(bank_statement_uid=bank_statement_uid)
    bank_statement_dataframe = pd.DataFrame(list(transactions.values()))

    if bank_statement_dataframe.empty:
        return Response({"error": "No transactions found for the given bank statement UID"}, status=status.HTTP_404_NOT_FOUND)

    bank_statement_dataframe['amount'] = pd.to_numeric(bank_statement_dataframe['amount'], errors='coerce')
    bank_statement_dataframe['money_in'] = pd.to_numeric(bank_statement_dataframe['money_in'], errors='coerce')
    bank_statement_dataframe['money_out'] = pd.to_numeric(bank_statement_dataframe['money_out'], errors='coerce')

    category_summary = bank_statement_dataframe.groupby('category').agg({
        'amount': 'sum',
        'money_in': 'sum',
        'money_out': 'sum',
        'currency': 'first'
    }).reset_index()

    category_summary.columns = ['Category', 'Total Amount', 'Money In', 'Money Out', 'Currency']

    for _, row in category_summary.iterrows():
        CategorisedTransaction.objects.create(
            bank_statement_uid=bank_statement_uid,
            category=row['Category'],
            total_amount=row['Total Amount'],
            money_in=row['Money In'],
            money_out=row['Money Out'],
            currency=row['Currency']
        )
    
    categorised_transactions = CategorisedTransaction.objects.filter(bank_statement_uid=bank_statement_uid)
    summary_dict = {
        'categories': [
            {
                'category': transaction.category,
                'total_amount': float(transaction.total_amount),
                'money_in': float(transaction.money_in) if transaction.money_in else None,
                'money_out': float(transaction.money_out) if transaction.money_out else None,
                'currency': transaction.currency
            }
            for transaction in categorised_transactions
        ]
    }
    
    return JsonResponse(summary_dict, status=status.HTTP_200_OK)