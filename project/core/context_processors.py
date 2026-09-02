# context_processors.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from .models import InternalOrder, ExternalOrder, PurchaseInvoice

def dashboard_counts(request):
    if not request.user.is_authenticated:
        return {}
    
    pending_internal_orders = InternalOrder.objects.filter(
        ~Q(status='received') & ~Q(status='cancelled')
    ).count()
    
    pending_external_orders = ExternalOrder.objects.filter(
        ~Q(status='received') & ~Q(status='cancelled')
    ).count()
    
    one_week_ago = timezone.now() - timedelta(days=7)
    pending_purchase_invoices = PurchaseInvoice.objects.filter(
        receive_date__gte=one_week_ago,
        status='confirmed'
    ).count()
    
    return {
        'pending_internal_orders': pending_internal_orders,
        'pending_external_orders': pending_external_orders,
        'pending_purchase_invoices': pending_purchase_invoices,
    }