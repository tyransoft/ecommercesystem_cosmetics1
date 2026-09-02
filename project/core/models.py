from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum

class Role(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'مدير النظام'
    EMPLOYEE = 'employee', 'موظف'


class CustomUser(AbstractUser):
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.EMPLOYEE, verbose_name='الدور')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def is_main_admin(self):
        return self.role == Role.SUPER_ADMIN

    def is_employee(self):
        return self.role == Role.EMPLOYEE
    


class Customer(models.Model):
    SOURSES = [
        ('facebook', 'فيسبوك'),
        ('instagram', 'إنستغرام'),
        ('tiktok', 'تيكتوك'),
        ('snapchat', 'سناب شات'),
        ('friend', 'صديق'), 
        ('advertisement', 'إعلان'),
        ('other', 'أخرى'),
    ]
    full_name = models.CharField(max_length=20, verbose_name='الاسم الكامل')
    phone = models.CharField(max_length=20, blank=True,null=True, verbose_name='رقم الهاتف')
    debt_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0,verbose_name='رصيد الدين')
    created_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL,null=True, blank=True, verbose_name='أنشأ بواسطة')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='المدينة')
    known_us_from = models.CharField(max_length=200,choices=SOURSES, blank=True, null=True, verbose_name='عرف عنا من')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'عميل'
        verbose_name_plural = 'العملاء'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name}-{self.city}- ({self.phone})"

    
    def get_all_orders(self):
        internal_orders = self.internalorder_set.all()
        external_orders = self.externalorder_set.all()
        return list(internal_orders) + list(external_orders)
    
    def get_total_orders_count(self):
        return self.internalorder_set.count() + self.externalorder_set.count()
    
    def get_received_orders_count(self):
        internal_received = self.internalorder_set.filter(status='received').count()
        external_received = self.externalorder_set.filter(status='received').count()
        return internal_received + external_received
    
    def get_completion_rate(self):
        total = self.get_total_orders_count()
        if total == 0:
            return 0
        received = self.get_received_orders_count()
        return round((received / total) * 100, 2)
    
    def get_first_order_date(self):
        internal_first = self.internalorder_set.filter(status__in=['confirmed', 'indelivery', 'received']).order_by('created_at').first()
        external_first = self.externalorder_set.filter(status__in=['confirmed','indelivery', 'received']).order_by('created_at').first()
        
        dates = []
        if internal_first:
            dates.append(internal_first.created_at)
        if external_first:
            dates.append(external_first.created_at)
        
        if dates:
            return min(dates)
        return None
    
    def get_last_order_date(self):
        internal_last = self.internalorder_set.filter(status__in=['confirmed', 'indelivery', 'received']).order_by('-created_at').first()
        external_last = self.externalorder_set.filter(status__in=['confirmed','indelivery', 'received']).order_by('-created_at').first()
        
        dates = []
        if internal_last:
            dates.append(internal_last.created_at)
        if external_last:
            dates.append(external_last.created_at)
        
        if dates:
            return max(dates)
        return None
    
    def get_total_spent(self):
        internal_total = self.internalorder_set.filter(status__in=['confirmed', 'indelivery', 'received']).aggregate(
            total=Sum('sales_total')
        )['total'] or Decimal('0')
        
        external_total = self.externalorder_set.filter(status__in=['confirmed','indelivery', 'received']).aggregate(
            total=Sum('lyd_sales_total')
        )['total'] or Decimal('0')
        
        return internal_total + external_total
    
    def get_total_profit(self):
        internal_profit = self.internalorder_set.filter(status__in=['confirmed', 'indelivery', 'received']).aggregate(
            total=Sum('total_profit')
        )['total'] or Decimal('0')
        
        external_profit = self.externalorder_set.filter(status__in=['confirmed','indelivery', 'received']).aggregate(
            total=Sum('lyd_commission_amount')
        )['total'] or Decimal('0')
        
        return internal_profit + external_profit
    
    def get_average_order_value(self):
        total_orders = self.get_total_orders_count()
        if total_orders == 0:
            return Decimal('0')
        return self.get_total_spent() / total_orders
    
    def get_most_requested_products(self, limit=5):
        from collections import Counter
        
        product_counter = Counter()
        
        internal_orders = self.internalorder_set.filter(status__in=['confirmed', 'indelivery', 'received'])
        for order in internal_orders:
            for item in order.items.all():
                product_counter[item.product.name] += item.quantity
        
        external_orders = self.externalorder_set.filter(status__in=['confirmed','indelivery', 'received'])
        for order in external_orders:
            for item in order.items.all():
                product_counter[item.product_name] += item.quantity
        
        return product_counter.most_common(limit)
    
    def get_most_requested_products_with_details(self, limit=5):
        from collections import defaultdict
        
        product_data = defaultdict(lambda: {'quantity': 0, 'revenue': 0})
        
        internal_orders = self.internalorder_set.filter(status__in=['confirmed', 'indelivery', 'received'])
        for order in internal_orders:
            for item in order.items.all():
                product_data[item.product.name]['quantity'] += item.quantity
                product_data[item.product.name]['revenue'] += item.total_price
        
        external_orders = self.externalorder_set.filter(status__in=['confirmed','indelivery', 'received'])
        for order in external_orders:
            for item in order.items.all():
                product_data[item.product_name]['quantity'] += item.quantity
                product_data[item.product_name]['revenue'] += item.total_price
        
        sorted_products = sorted(product_data.items(), key=lambda x: x[1]['quantity'], reverse=True)[:limit]
        
        return [
            {
                'name': name,
                'quantity': data['quantity'],
                'revenue': data['revenue']
            }
            for name, data in sorted_products
        ]   


class CustomerPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ المسدد')
    payment_date = models.DateTimeField(default=timezone.now, verbose_name='تاريخ التسديد')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, verbose_name='رقم الإيصال')
    created_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, verbose_name='تم بواسطة')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'تسديد دين عميل'
        verbose_name_plural = 'تسديدات ديون العملاء'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.amount} - {self.payment_date}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self._generate_receipt_number()
        super().save(*args, **kwargs)
    
    def _generate_receipt_number(self):
        date_str = timezone.now().strftime('%Y%m%d')
        count = CustomerPayment.objects.filter(
            payment_date__date=timezone.now().date()
        ).count() + 1
        return f"{date_str}{count:04d}"







class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم الفئة')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فئة'
        verbose_name_plural = 'الفئات'
        ordering = ['name']

    def __str__(self):
        return self.name





class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم المنتج')
    barcode = models.CharField(max_length=100, blank=True, verbose_name='الباركود')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,verbose_name='الفئة', related_name='products')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True, verbose_name='صورة المنتج')
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name='الماركة')
    color = models.CharField(max_length=20,blank=True,null=True , verbose_name='لون/درجة')
    made_in = models.CharField(max_length=100, blank=True, null=True, verbose_name='صنع في')

    usd_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر البيع بالدولار')
    lyd_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر البيع بالدينار')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'
        ordering = ['name']

    @staticmethod
    def generate_barcode():
        while True:
            barcode = ''.join(str(random.randint(0, 9)) for _ in range(5))
            if not Product.objects.filter(barcode=barcode).exists():
                return barcode

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.name} ({self.barcode})"


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='المنتج', related_name='inventory')
    quantity = models.PositiveIntegerField(default=0, verbose_name='الكمية')

    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر الصرف')

    lyd_buy_coast_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='تكلفة الشراء بالدينار')
    lyd_shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='تكلفة الشحن بالدينار')
    lyd_total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='التكلفة الإجمالية بالدينار')

    usd_buy_coast_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='تكلفة الشراء بالدولار')
    usd_shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='تكلفة الشحن بالدولار')
    usd_total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='التكلفة الإجمالية بالدولار')

    usd_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر البيع بالدولار')
    lyd_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر البيع بالدينار')


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'المخزون'
        verbose_name_plural = 'المخزون'
        ordering = ['product']


    def get_movement_status(self):
        if self.quantity == 0:
            return {
                'status': 'منتهي',
                'class': 'bg-error/10 text-error',
                'badge_class': 'bg-error text-white'
            }
        
        ninety_days_ago = timezone.now() - timedelta(days=90)
        
        total_sold = InventoryMovement.objects.filter(
            product=self.product,
            movement_type='sale',
            created_at__gte=ninety_days_ago
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        total_sold = abs(total_sold)
        
        if total_sold == 0 or  1 <= total_sold <= 3:
            return {
                'status': 'راكد',
                'class': 'bg-error/10 text-error',
                'badge_class': 'bg-error text-white'
            }
        elif 4 <= total_sold <= 20:
            return {
                'status': 'حركة منخفضة',
                'class': 'bg-warning/10 text-warning',
                'badge_class': 'bg-warning text-white'
            }
        elif 21 <= total_sold <= 35:
            return {
                'status': 'حركة متوسطة',
                'class': 'bg-primary/10 text-primary',
                'badge_class': 'bg-primary text-white'
            }
        elif 40 <= total_sold <= 55:
            return {
                'status': 'حركة جيدة',
                'class': 'bg-success/10 text-success',
                'badge_class': 'bg-success text-white'
            }
        else:
            return {
                'status': 'حركة غزيرة',
                'class': 'bg-blue-500/10 text-blue-500',
                'badge_class': 'bg-blue-500 text-white'
            }

    def get_sold_quantity_last_90_days(self):
        ninety_days_ago = timezone.now() - timedelta(days=90)
        total_sold = InventoryMovement.objects.filter(
            product=self.product,
            movement_type='sale',
            created_at__gte=ninety_days_ago
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        return abs(total_sold)
    
    def save(self, *args, **kwargs):
      self.lyd_sell_price = self.product.lyd_sell_price
      self.usd_sell_price = self.product.usd_sell_price
    
      super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"



class InventoryMovement(models.Model):
    MOVEMENT_TYPES = [
        ('sale', 'بيع'),
        ('purchase','شراء'),
        ('gift', 'هدية'),
        ('test', 'عينة تجريبية'),
        ('adjustment', 'تعديل'),
        ('damage','تلف'),
        ('returned','راجع'),
        ('stock_addition','جرد موجب'),
        ('stock_deduction','جرد سالب'),


    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"



class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم المورد')
    debt_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='رصيد الدين')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'مورد'
        verbose_name_plural = 'الموردين'
        ordering = ['name']
    
    def update_debt_balance(self):
        from django.db.models import Sum, F, Case, When, Value, DecimalField, Q
        
        result = PurchaseInvoice.objects.filter(
            supplier=self,
            status='confirmed'
        ).aggregate(
            total_debt=Sum('debt_amount')
        )
        
        self.debt_balance = result['total_debt'] or 0
        self.save(update_fields=['debt_balance'])
    
    def get_pending_invoices(self):
        return PurchaseInvoice.objects.filter(
            supplier=self,
            status='confirmed',
            debt_amount__gt=0
        ).order_by('created_at')

    def __str__(self):
        return self.name

class SupplierPayment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'نقدي'),
        ('bank', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('other', 'أخرى'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='المبلغ')
    payment_date = models.DateField(default=timezone.now, verbose_name='تاريخ السداد')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name='طريقة الدفع')
    reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='رقم المرجع')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True, verbose_name='تم بواسطة')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'سداد مورد'
        verbose_name_plural = 'سدديات الموردين'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.supplier.name} - {self.amount} - {self.payment_date}"
    


class PurchaseInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكدة'),
        ('cancelled', 'ملغاة'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ المدفوع')
    debt_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ المتبقي')
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='تكلفة الشحن')

    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر الصرف')

    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    notes = models.TextField(blank=True)
    receive_date = models.DateTimeField(verbose_name='تاريخ الوصول')
    
    created_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        verbose_name = 'فاتورة مشتريات'
        verbose_name_plural = 'فواتير المشتريات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invoice_number}"
    

    def save(self, *args, **kwargs):
      if not self.invoice_number :
        self.invoice_number = self._generate_invoice_number()
    
      self.debt_amount = self.total - self.paid_amount
    
      if self.debt_amount < 0:
        self.debt_amount = 0
    
      super().save(*args, **kwargs)
    
      if self.supplier and self.status == 'confirmed':
        self.supplier.update_debt_balance()
    def _generate_invoice_number(self):
        date_str = timezone.now().strftime('%Y%m%d')
        count = PurchaseInvoice.objects.filter(
            created_at__date=timezone.now().date(),
        ).count() + 1
        return f"P{date_str}{count:04d}"
    

    


class PurchaseInvoiceItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_lyd = models.DecimalField(max_digits=12, decimal_places=2)
    unit_usd = models.DecimalField(max_digits=12, decimal_places=2)
    unit_shipping_cost_lyd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_shipping_cost_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_lyd_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_usd_price = models.DecimalField(max_digits=12, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر الصرف')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'بند فاتورة مشتريات'
        verbose_name_plural = 'بنود فواتير المشتريات'
    
    def save(self, *args, **kwargs):
        self.total_usd_price = (self.unit_usd * self.quantity) + (self.unit_shipping_cost_usd * self.quantity)
        self.total_lyd_price= self.total_usd_price * self.exchange_rate
        super().save(*args, **kwargs)    



class ExpenseCategory(models.Model):
    name = models.CharField(max_length=200, verbose_name='اسم الفئة')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فئة مصروف'
        verbose_name_plural = 'فئات المصروفات'

    def __str__(self):
        return self.name

    @property
    def total_expenses(self):
        return self.expenses.aggregate(total=models.Sum('amount'))['total'] or 0


class Expense(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان المصروف')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='المبلغ')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses', verbose_name='الفئة')
    payment_method = models.CharField(max_length=20, choices=[('cash', 'نقدي'), ('bank', 'تحويل بنكي'), ('check', 'شيك'), ('other', 'أخرى')], default='cash', verbose_name='طريقة الدفع')
    description = models.TextField(blank=True, null=True, verbose_name='الوصف')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='سجّل بواسطة')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مصروف'
        verbose_name_plural = 'المصروفات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount}"            



class InternalOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكدة'),
        ('indelivery','قيد التوصيل'),
        ('received','تم الاستلام'),

        ('cancelled', 'ملغاة'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ المدفوع')
    debt_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ المتبقي') 
    delivery_address = models.CharField(max_length=200, blank=True, null=True, verbose_name='عنوان التوصيل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الربح')
    created_at = models.DateTimeField(auto_now_add=True)
    indelivery_at=models.DateTimeField()
    @staticmethod
    def generate_ordernumber():
        while True:
            order_number = ''.join(str(random.randint(0, 9)) for _ in range(5))
            if not ExternalOrder.objects.filter(order_number=order_number).exists():
                return order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_ordernumber()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.order_number} - {self.customer.full_name if self.customer else 'عميل غير محدد'}"
    def get_days_in_indelivery(self):
        if self.status == 'indelivery' and self.indelivery_at:
            delta = timezone.now() - self.indelivery_at
            return delta.days
        elif self.status == 'received' and self.indelivery_at:
            delta = self.received_at - self.indelivery_at
            return delta.days
        return 0
    
    def get_hours_in_indelivery(self):
        if self.status == 'indelivery' and self.indelivery_at:
            delta = timezone.now() - self.indelivery_at
            return delta.total_seconds() / 3600

        return 0
    
    def get_indelivery_duration_display(self):
        days = self.get_days_in_indelivery()
        hours = self.get_hours_in_indelivery()
        
        if days == 0 and hours < 24:
            return f"{int(hours)} ساعة"
        elif days == 0:
            return "أقل من يوم"
        elif days == 1:
            return "يوم واحد"
        else:
            return f"{days} أيام"


class InternalOrderItem(models.Model):
    order = models.ForeignKey(InternalOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = 'بند طلب '
        verbose_name_plural = 'بنود الطلبات '    

class ExternalOrderCommission(models.Model):
    name = models.CharField(max_length=100, verbose_name='اسم العمولة')
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='من قيمة ($)')
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='إلى قيمة ($)')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة العمولة %')
    fixed_amount_lyd = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='قيمة ثابتة (دينار)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['min_amount']
        verbose_name = 'عمولة الطلبات الخارجية'
        verbose_name_plural = 'عمولات الطلبات الخارجية'

    def __str__(self):
        if self.fixed_amount_lyd > 0:
            return f'{self.name} - {self.percentage}% + {self.fixed_amount_lyd} د.ل'
        return f'{self.name} - {self.percentage}%'
    
    def calculate_commission(self, amount_usd, exchange_rate):
        from decimal import Decimal
        
        amount_usd = Decimal(str(amount_usd))
        exchange_rate = Decimal(str(exchange_rate))
        percentage = Decimal(str(self.percentage))
        fixed_amount_lyd = Decimal(str(self.fixed_amount_lyd))
        
        percentage_amount_usd = amount_usd * (percentage / Decimal('100'))
        percentage_amount_lyd = percentage_amount_usd * exchange_rate
        total_lyd = percentage_amount_lyd + fixed_amount_lyd
        total_usd = total_lyd / exchange_rate if exchange_rate > 0 else Decimal('0')
        
        return {
            'usd': total_usd,
            'lyd': total_lyd,
            'percentage_amount_usd': percentage_amount_usd,
            'percentage_amount_lyd': percentage_amount_lyd,
            'fixed_amount_lyd': fixed_amount_lyd
        }
class ExternalOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('indeliver', 'في التوصيل'),
        ('confirmed', 'مؤكدة'),
        ('received', 'مستلمة'),
        ('cancelled', 'ملغاة'),


    ]
    SUPPLY=[
      ('alibaba','علي بابا'),
      ('amazon','امازون'),
      ('noon','نون'),
      ('shein','شي ان'),
      ('1168','1168'),
      ('others','اخرى'),


    ]
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supply=models.CharField(max_length=20,choices=SUPPLY, default='others')
    usd_sales_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lyd_sales_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    lyd_paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ المدفوع')
    lyd_debt_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='المبلغ المتبقي') 
    delivery_address = models.CharField(max_length=200, blank=True, null=True, verbose_name='عنوان التوصيل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='سعر الصرف')

    commission_rule = models.ForeignKey(ExternalOrderCommission,on_delete=models.SET_NULL,null=True,blank=True,related_name='orders',verbose_name='قاعدة العمولة')
    commission_percentage = models.DecimalField(max_digits=5,decimal_places=2,default=0,verbose_name='نسبة العمولة')
    lyd_commission_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0,verbose_name='قيمة العمولة')

    usd_shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='تكلفة الشحن بالدولار')
    lyd_shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='تكلفة الشحن بالدينار')
    
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='إجمالي الربح')
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_ordernumber():
        while True:
            order_number = ''.join(str(random.randint(0, 9)) for _ in range(5))
            if not ExternalOrder.objects.filter(order_number=order_number).exists():
                return order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_ordernumber()
        self.total_profit = self.lyd_commission_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.customer.full_name if self.customer else 'عميل غير محدد'}"


    
class ExternalOrderItem(models.Model):
    order = models.ForeignKey(ExternalOrder, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200, verbose_name='اسم المنتج')
    product_link = models.CharField(max_length=200,null=True, blank=True, verbose_name='رابط المنتج')
    quantity = models.IntegerField()
    usd_unit_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lyd_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    lyd_total_price = models.DecimalField(max_digits=12, decimal_places=2)
    usd_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    usd_total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'بند طلب '
        verbose_name_plural = 'بنود الطلبات '