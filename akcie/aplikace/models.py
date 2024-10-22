from django.db import models

class Stock(models.Model):
    ticker = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    last_price = models.FloatField(null=True, blank=True)
    market_cap = models.FloatField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    ebitda = models.FloatField(null=True, blank=True)
    beta = models.FloatField(null=True, blank=True)
    enterprise_value = models.FloatField(null=True, blank=True)
    # Přidání základních informací z yFinance nebo SimFin (nepovinně)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)

class IncomeStatement(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    fiscal_year = models.IntegerField()
    revenue = models.FloatField(null=True, blank=True)
    gross_profit = models.FloatField(null=True, blank=True)
    operating_income = models.FloatField(null=True, blank=True)
    net_income = models.FloatField(null=True, blank=True)
    ebitda = models.FloatField(null=True, blank=True)
    operating_expenses = models.FloatField(null=True, blank=True)
    cost_of_revenue = models.FloatField(null=True, blank=True)
    interest_expense = models.FloatField(null=True, blank=True)


class BalanceSheet(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    fiscal_year = models.IntegerField()
    total_assets = models.FloatField(null=True, blank=True)
    total_liabilities = models.FloatField(null=True, blank=True)
    total_equity = models.FloatField(null=True, blank=True)
    cash_and_equivalents = models.FloatField(null=True, blank=True)
    short_term_debt = models.FloatField(null=True, blank=True)
    long_term_debt = models.FloatField(null=True, blank=True)
    accounts_receivable = models.FloatField(null=True, blank=True)
    inventories = models.FloatField(null=True, blank=True)
    retained_earnings = models.FloatField(null=True, blank=True)


class CashFlowStatement(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    fiscal_year = models.IntegerField()
    operating_cash_flow = models.FloatField(null=True, blank=True)
    investing_cash_flow = models.FloatField(null=True, blank=True)
    financing_cash_flow = models.FloatField(null=True, blank=True)
    free_cash_flow = models.FloatField(null=True, blank=True)
    capital_expenditures = models.FloatField(null=True, blank=True)


class SharePrices(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    date = models.DateField()
    close_price = models.FloatField(null=True, blank=True)
    open_price = models.FloatField(null=True, blank=True)
    high_price = models.FloatField(null=True, blank=True)
    low_price = models.FloatField(null=True, blank=True)
    volume = models.FloatField(null=True, blank=True)


class CompanyInformation(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    founded_year = models.IntegerField(null=True, blank=True)
    employees = models.IntegerField(null=True, blank=True)
    headquarters = models.CharField(max_length=255, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
