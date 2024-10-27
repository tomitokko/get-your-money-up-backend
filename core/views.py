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
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings


def forecast_leftover(bank_statement_uid):
    months_ahead = 12
    bank_statement_transactions = Transaction.objects.filter(bank_statement_uid=bank_statement_uid)
    bank_statement_dataframe = pd.DataFrame(list(bank_statement_transactions.values()))
    try:
        data = bank_statement_dataframe
    except pd.errors.EmptyDataError:
        raise ValueError(f"The file data is empty.")
    data = bank_statement_dataframe


    required_columns = {'date', 'time', 'category', 'amount'}
    if not required_columns.issubset(data.columns):
        missing = required_columns - set(data.columns)
        raise ValueError(f"The following required columns are missing from the CSV: {missing}")


    try:
        
        data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d', errors='coerce')
        if data['date'].isnull().any():
            raise ValueError("Some dates in the 'Date' column could not be parsed. Ensure they are in 'YYYY-MM-DD' format.")

        data['Year'] = data['date'].dt.year
        data['Month'] = data['date'].dt.month

        data['YearMonth'] = data['date'].dt.to_period('M').astype(str)

        monthly_summary = data.groupby('YearMonth').agg(
            Total_Income=('amount', lambda x: x[data['category'].str.lower() == 'income'].sum()),
            Total_Expenses=('amount', lambda x: x[data['category'].str.lower() != 'income'].sum())
        ).reset_index()

        monthly_summary['Leftover'] = monthly_summary['Total_Income'] - monthly_summary['Total_Expenses']

        monthly_summary['YearMonthPeriod'] = pd.PeriodIndex(monthly_summary['YearMonth'], freq='M')
        monthly_summary.sort_values('YearMonthPeriod', inplace=True)
        monthly_summary.set_index('YearMonthPeriod', inplace=True)

        leftover_series = monthly_summary['Leftover']
    except Exception as e:
        raise ValueError(f"Error processing data: {e}")

    if leftover_series.empty:
        raise ValueError("No data available to calculate leftovers.")
    if len(leftover_series) < 2:
        raise ValueError("Not enough data points to fit the SARIMA model.")

    try:
        # Define SARIMA parameters
        order = (2, 1, 2)  # (p, d, q)
        seasonal_order = (1, 1, 1, 12)  # (P, D, Q, s)

        # Initialize the SARIMA model
        model = SARIMAX(leftover_series, order=order, seasonal_order=seasonal_order)

        # Suppress convergence warnings temporarily
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            model_fit = model.fit(disp=False)

        # Check if the model converged
        if not model_fit.mle_retvals['converged']:
            # Handle non-convergence silently or consider alternative approaches
            pass 
    except Exception as e:
        raise RuntimeError(f"Failed to fit SARIMA model: {e}")

    # Step 6: Forecast future months
    try:
        forecast = model_fit.forecast(steps=months_ahead)
        forecast_rounded =[round(value,2) for value in forecast]
    except Exception as e:
        raise RuntimeError(f"Failed to forecast using SARIMA model: {e}")

    print(forecast_rounded)
    return forecast_rounded


@api_view(['POST'])
def create_transaction(request):
    statements = request.data.get('statements', [])
    created_transactions = []

    for statement in statements:
        serializer = TransactionSerializer(data=statement)
        if serializer.is_valid():
            serializer.save()
            created_transactions.append(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if statements:
        bank_statement_uid = statements[0].get('bank_statement_uid')
        if bank_statement_uid is None:
            return Response({"error": "bank_statement_uid is missing from the statement"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "No statements provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    # forecast_leftover(bank_statement_uid)
    return Response(created_transactions, status=status.HTTP_201_CREATED)

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


