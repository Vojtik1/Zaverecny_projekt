from django.contrib import admin
from .models import Stock, IncomeStatement, BalanceSheet, CashFlowStatement, SharePrices, CustomUser, Portfolio, \
    PortfolioStock

admin.site.register(Stock)
admin.site.register(IncomeStatement)
admin.site.register(BalanceSheet)
admin.site.register(CashFlowStatement)
admin.site.register(SharePrices)
admin.site.register(CustomUser)
admin.site.register(PortfolioStock)

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_shared')
    list_filter = ('is_shared',)

