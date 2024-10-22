import simfin as sf
import csv
import yfinance as yf
from django.shortcuts import render
from simfin.names import *
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.http import HttpResponse
from .models import Stock, IncomeStatement, BalanceSheet, CashFlowStatement, SharePrices

sf.set_api_key('dacb95bc-907f-47cc-8c2d-2504aa3d32dd')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
simfin_data_path = os.path.join(BASE_DIR, 'simfin_data')
sf.set_data_dir(simfin_data_path)

# Kontrola a automatické stažení dat, pokud nejsou přítomná
datasets = [
    ('income', 'annual'),
    ('balance', 'annual'),
    ('cashflow', 'annual'),
    ('shareprices', 'daily')
]

for dataset_name, variant in datasets:
    dataset_path = os.path.join(simfin_data_path, f'us-{dataset_name}-{variant}.csv')
    if not os.path.exists(dataset_path):
        print(f"Dataset {dataset_name} není nalezen. Stahování ze SimFin API...")
        sf.load(dataset=dataset_name, variant=variant, market='us', index=['Ticker', 'Fiscal Year'])

def create_price_chart(close_prices):
    dates = [price['date'] for price in close_prices]
    prices = [price['close_price'] for price in close_prices]

    # Vytvoření grafu
    fig, ax = plt.subplots()
    ax.plot(dates, prices, label='Close Price')

    ax.set(xlabel='Date', ylabel='Close Price',
           title='Stock Price Over Time')
    ax.grid()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return image_base64

def home(request):
    stocks = Stock.objects.all()
    if request.method == 'GET':
        market_cap_min = request.GET.get('market_cap_min')
        market_cap_max = request.GET.get('market_cap_max')

        if market_cap_min:
            stocks = stocks.filter(market_cap__gte=market_cap_min)
        if market_cap_max:
            stocks = stocks.filter(market_cap__lte=market_cap_max)

    # Výpočet průměrné návratnosti
    average_return = None
    if stocks.exists():
        total_return = 0
        count = 0
        for stock in stocks:
            share_prices = SharePrices.objects.filter(stock=stock).order_by('date')
            if share_prices.count() > 1:
                first_price = share_prices.first().close_price
                last_price = share_prices.last().close_price
                if first_price and last_price and first_price != 0:
                    total_return += (last_price - first_price) / first_price
                    count += 1
        if count > 0:
            average_return = (total_return / count) * 100

    context = {
        'stocks': stocks,
        'average_return': average_return
    }

    return render(request, 'home.html', context)

def format_large_numbers(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value

    sign = '-' if value < 0 else ''
    value = abs(value)

    if value >= 1_000_000_000_000:
        return f'{sign}{value / 1_000_000_000_000:.1f}T'
    elif value >= 1_000_000_000:
        return f'{sign}{value / 1_000_000_000:.1f}B'
    elif value >= 1_000_000:
        return f'{sign}{value / 1_000_000:.1f}M'
    elif value >= 1_000:
        return f'{sign}{value / 1_000:.1f}K'
    return f'{sign}{value:.2f}'

def stock_detail(request, ticker):
    stock_data_yf = yf.Ticker(ticker)
    yf_info = stock_data_yf.info

    # Nejprve načteme nebo vytvoříme záznam pro Stock
    stock, created = Stock.objects.get_or_create(ticker=ticker)
    stock.name = yf_info.get('shortName')
    stock.last_price = yf_info.get('currentPrice') or yf_info.get('regularMarketPrice') or yf_info.get('previousClose')
    stock.market_cap = yf_info.get('marketCap')
    stock.pe_ratio = yf_info.get('trailingPE')
    stock.ebitda = yf_info.get('ebitda')
    stock.beta = yf_info.get('beta')
    stock.enterprise_value = yf_info.get('enterpriseValue')
    stock.sector = yf_info.get('sector')
    stock.industry = yf_info.get('industry')
    stock.save()

    share_prices = SharePrices.objects.filter(stock=stock)

    close_prices = [
        {'date': price.date, 'close_price': price.close_price}
        for price in share_prices
    ]
    chart_image = create_price_chart(close_prices)

    try:
        # Načítání dat z datasetů s víceúrovňovým indexem
        income_df = sf.load(dataset='income', variant='annual', market='us', index=['Ticker', 'Fiscal Year'])
        balance_df = sf.load(dataset='balance', variant='annual', market='us', index=['Ticker', 'Fiscal Year'])
        cashflow_df = sf.load(dataset='cashflow', variant='annual', market='us', index=['Ticker', 'Fiscal Year'])

        # Income Statement
        if ticker in income_df.index.get_level_values('Ticker'):
            income_data = income_df.loc[ticker]
            for year in income_data.index.get_level_values('Fiscal Year'):
                IncomeStatement.objects.update_or_create(
                    stock=stock,
                    fiscal_year=year,
                    defaults={
                        'revenue': income_data.loc[year, 'Revenue'] if 'Revenue' in income_data.columns else None,
                        'gross_profit': income_data.loc[year, 'Gross Profit'] if 'Gross Profit' in income_data.columns else None,
                        'net_income': income_data.loc[year, 'Net Income'] if 'Net Income' in income_data.columns else None,
                        'ebitda': (income_data.loc[year, 'Operating Income (Loss)'] + income_data.loc[year, 'Depreciation & Amortization']) if 'Operating Income (Loss)' in income_data.columns and 'Depreciation & Amortization' in income_data.columns else None,
                        'operating_income': income_data.loc[year, 'Operating Income (Loss)'] if 'Operating Income (Loss)' in income_data.columns else None,
                        'operating_expenses': income_data.loc[year, 'Operating Expenses'] if 'Operating Expenses' in income_data.columns else None,
                        'cost_of_revenue': income_data.loc[year, 'Cost of Revenue'] if 'Cost of Revenue' in income_data.columns else None,
                        'interest_expense': income_data.loc[year, 'Interest Expense, Net'] if 'Interest Expense, Net' in income_data.columns else None
                    }
                )

        # Balance Sheet
        if ticker in balance_df.index.get_level_values('Ticker'):
            balance_data = balance_df.loc[ticker]
            for year in balance_data.index.get_level_values('Fiscal Year'):
                BalanceSheet.objects.update_or_create(
                    stock=stock,
                    fiscal_year=year,
                    defaults={
                        'total_assets': balance_data.loc[year, 'Total Assets'] if 'Total Assets' in balance_data.columns else None,
                        'total_liabilities': balance_data.loc[year, 'Total Liabilities'] if 'Total Liabilities' in balance_data.columns else None,
                        'total_equity': balance_data.loc[year, 'Total Equity'] if 'Total Equity' in balance_data.columns else None,
                        'cash_and_equivalents': balance_data.loc[year, 'Cash, Cash Equivalents & Short Term Investments'] if 'Cash, Cash Equivalents & Short Term Investments' in balance_data.columns else None,
                        'short_term_debt': balance_data.loc[year, 'Short Term Debt'] if 'Short Term Debt' in balance_data.columns else None,
                        'long_term_debt': balance_data.loc[year, 'Long Term Debt'] if 'Long Term Debt' in balance_data.columns else None
                    }
                )

        # Cash Flow Statement
        if ticker in cashflow_df.index.get_level_values('Ticker'):
            cashflow_data = cashflow_df.loc[ticker]
            for year in cashflow_data.index.get_level_values('Fiscal Year'):
                # Zkontrolujeme, zda jsou dostupná data pro jednotlivé ukazatele
                operating_cash_flow = cashflow_data.loc[
                    year, 'Net Cash from Operating Activities'] if 'Net Cash from Operating Activities' in cashflow_data.columns else None
                investing_cash_flow = cashflow_data.loc[
                    year, 'Net Cash from Investing Activities'] if 'Net Cash from Investing Activities' in cashflow_data.columns else None
                financing_cash_flow = cashflow_data.loc[
                    year, 'Net Cash from Financing Activities'] if 'Net Cash from Financing Activities' in cashflow_data.columns else None

                # Pokud 'Free Cash Flow' není v datasetu, vypočítáme jej z operativního cashflow a CAPEX (pokud je CAPEX dostupný)
                if 'Free Cash Flow' in cashflow_data.columns:
                    free_cash_flow = cashflow_data.loc[year, 'Free Cash Flow']
                elif 'Capital Expenditures' in cashflow_data.columns:
                    free_cash_flow = operating_cash_flow - cashflow_data.loc[
                        year, 'Capital Expenditures'] if operating_cash_flow is not None else None
                else:
                    free_cash_flow = None  # Nastavíme na None, pokud není možné spočítat FCF

                # Uložení dat do databáze
                CashFlowStatement.objects.update_or_create(
                    stock=stock,
                    fiscal_year=year,
                    defaults={
                        'operating_cash_flow': operating_cash_flow,
                        'investing_cash_flow': investing_cash_flow,
                        'financing_cash_flow': financing_cash_flow,
                        'free_cash_flow': free_cash_flow
                    }
                )

    except Exception as e:
        print(f"Error loading SimFin data for {ticker}: {e}")

    context = {
        'stock': stock,
        'income_statements': [
            {
                'fiscal_year': statement.fiscal_year,
                'revenue': format_large_numbers(statement.revenue),
                'gross_profit': format_large_numbers(statement.gross_profit),
                'operating_income': format_large_numbers(statement.operating_income),
                'net_income': format_large_numbers(statement.net_income)
            }
            for statement in IncomeStatement.objects.filter(stock=stock)
        ],
        'balance_sheets': [
            {
                'fiscal_year': statement.fiscal_year,
                'total_assets': format_large_numbers(statement.total_assets),
                'total_liabilities': format_large_numbers(statement.total_liabilities),
                'total_equity': format_large_numbers(statement.total_equity),
                'cash_and_equivalents': format_large_numbers(statement.cash_and_equivalents),
                'short_term_debt': format_large_numbers(statement.short_term_debt),
                'long_term_debt': format_large_numbers(statement.long_term_debt)
            }
            for statement in BalanceSheet.objects.filter(stock=stock)
        ],
        'cash_flow_statements': [
            {
                'fiscal_year': statement.fiscal_year,
                'operating_cash_flow': format_large_numbers(statement.operating_cash_flow),
                'investing_cash_flow': format_large_numbers(statement.investing_cash_flow),
                'financing_cash_flow': format_large_numbers(statement.financing_cash_flow)
            }
            for statement in CashFlowStatement.objects.filter(stock=stock)
        ],
        'share_prices': [
            {
                'date': statement.date,
                'close_price': statement.close_price,
                'volume': statement.volume
            }
            for statement in SharePrices.objects.filter(stock=stock)
        ],
        'chart_image': chart_image
    }

    return render(request, 'stock_detail.html', context)
