from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Transaction, CategorisedTransaction
from .serializers import TransactionSerializer
import pandas as pd
import os
from django.conf import settings

@api_view(['POST'])
def create_transaction(request):
    serializer = TransactionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# summarize bank statements based on categories
def summarize_bank_statement(request, bank_statement_uid='bdb9c0fc-f0c2-4d8e-9073-c156e50f3395'):
    # bank_statement_file_path = os.path.join(settings.MEDIA_ROOT, 'bank_statement.csv')

    # Filter transactions based on the provided bank_statement_uid
    transactions = Transaction.objects.filter(bank_statement_uid=bank_statement_uid)

    # Create a DataFrame from the filtered transactions
    bank_statement_dataframe = pd.DataFrame(list(transactions.values()))

    if bank_statement_dataframe.empty:
        return Response({"error": "No transactions found for the given bank statement UID"}, status=status.HTTP_404_NOT_FOUND)

    # Ensure numeric types for calculations
    bank_statement_dataframe['amount'] = pd.to_numeric(bank_statement_dataframe['amount'], errors='coerce')
    bank_statement_dataframe['money_in'] = pd.to_numeric(bank_statement_dataframe['money_in'], errors='coerce')
    bank_statement_dataframe['money_out'] = pd.to_numeric(bank_statement_dataframe['money_out'], errors='coerce')

    # Group by category and calculate summaries
    category_summary = bank_statement_dataframe.groupby('category').agg({
        'amount': 'sum',
        'money_in': 'sum',
        'money_out': 'sum',
        'currency': 'first'  # Assuming currency is consistent within categories
    }).reset_index()

    category_summary.columns = ['Category', 'Total Amount', 'Money In', 'Money Out', 'Currency']


    # bank_statement_file_path = request.build_absolute_uri('/media/bank_statement.csv')
    # bank_statement_dataframe = pd.read_csv(bank_statement_file_path)
    
    # bank_statement_dataframe['Amount'] = pd.to_numeric(bank_statement_dataframe['Amount'], errors='coerce')

    # Calculate money_in and money_out for each category
    # bank_statement_dataframe['Money In'] = pd.to_numeric(bank_statement_dataframe['Money In'], errors='coerce')
    # bank_statement_dataframe['Money out'] = pd.to_numeric(bank_statement_dataframe['Money out'], errors='coerce')

    # category_summary = bank_statement_dataframe.groupby('Category').agg({
    #     'Amount': 'sum',
    #     'Money In': 'sum',
    #     'Money out': 'sum',
    #     'Currency': 'first'  # Assuming currency is consistent within categories
    # }).reset_index()

    # category_summary.columns = ['Category', 'Total Amount', 'Money In', 'Money Out', 'Currency']

    # Create CategorisedTransaction objects
    for _, row in category_summary.iterrows():
        CategorisedTransaction.objects.create(
            bank_statement_uid=bank_statement_uid,
            category=row['Category'],
            total_amount=row['Total Amount'],
            money_in=row['Money In'],
            money_out=row['Money Out'],
            currency=row['Currency']
        )

    # category_summary = bank_statement_dataframe.groupby('Category')['Amount'].agg(['sum', 'count']).reset_index()


    # category_summary.columns = ['Category', 'Total Amount', 'Number of Transactions']

    # category_summary = category_summary.sort_values('Total Amount', ascending=False)

    # summary_dict = category_summary.to_dict('records')
    # print(summary_dict)

    # return render(request, 'summary.html', {'summary': summary_dict})