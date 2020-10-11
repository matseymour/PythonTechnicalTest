from django.contrib import admin

from .models import Bond


@admin.register(Bond)
class BondAdmin(admin.ModelAdmin):

    fieldsets = (
        (None, {'fields': ('owner', 'isin', 'size', 'currency', 'maturity', 'lei', 'legal_name')}),
    )
