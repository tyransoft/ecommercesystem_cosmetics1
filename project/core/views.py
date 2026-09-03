from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from .forms import *
from django.core.paginator import Paginator
from decimal import Decimal
from django.db.models import Q ,Sum, Count,F
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta,time
from django.utils import timezone
from .models import *
from collections import defaultdict

def home(request):

    today = timezone.now().date()
    first_day_month = today.replace(day=1)
    last_month = first_day_month - timedelta(days=1)
    first_day_last_month = last_month.replace(day=1)
    
    total_products = Product.objects.count()
    total_orders = InternalOrder.objects.count() + ExternalOrder.objects.count()
    
    current_month_sales_internal = InternalOrder.objects.filter(
        created_at__date__gte=first_day_month,
        status__in=['confirmed', 'indelivery', 'received']
    ).aggregate(total=Sum('sales_total'))['total'] or Decimal('0')
    
    current_month_sales_external = ExternalOrder.objects.filter(
        created_at__date__gte=first_day_month,
        status__in=['confirmed', 'indeliver', 'received']
    ).aggregate(total=Sum('lyd_sales_total'))['total'] or Decimal('0')
    
    current_month_sales = current_month_sales_internal + current_month_sales_external
    
    last_month_sales_internal = InternalOrder.objects.filter(
        created_at__date__gte=first_day_last_month,
        created_at__date__lte=last_month,
        status__in=['confirmed', 'indelivery', 'received']
    ).aggregate(total=Sum('sales_total'))['total'] or Decimal('0')
    
    last_month_sales_external = ExternalOrder.objects.filter(
        created_at__date__gte=first_day_last_month,
        created_at__date__lte=last_month,
        status__in=['confirmed', 'indeliver', 'received']
    ).aggregate(total=Sum('lyd_sales_total'))['total'] or Decimal('0')
    
    last_month_sales = last_month_sales_internal + last_month_sales_external
    
    sales_change = 0
    if last_month_sales > 0:
        sales_change = round(((current_month_sales - last_month_sales) / last_month_sales) * 100, 2)
    
    current_month_profit_internal = InternalOrder.objects.filter(
        created_at__date__gte=first_day_month,
        status__in=['confirmed', 'indelivery', 'received']
    ).aggregate(total=Sum('total_profit'))['total'] or Decimal('0')
    
    current_month_profit_external = ExternalOrder.objects.filter(
        created_at__date__gte=first_day_month,
        status__in=['confirmed', 'indeliver', 'received']
    ).aggregate(total=Sum('lyd_commission_amount'))['total'] or Decimal('0')
    
    current_month_profit = current_month_profit_internal + current_month_profit_external
    
    last_month_profit_internal = InternalOrder.objects.filter(
        created_at__date__gte=first_day_last_month,
        created_at__date__lte=last_month,
        status__in=['confirmed', 'indelivery', 'received']
    ).aggregate(total=Sum('total_profit'))['total'] or Decimal('0')
    
    last_month_profit_external = ExternalOrder.objects.filter(
        created_at__date__gte=first_day_last_month,
        created_at__date__lte=last_month,
        status__in=['confirmed', 'indeliver', 'received']
    ).aggregate(total=Sum('lyd_commission_amount'))['total'] or Decimal('0')
    
    last_month_profit = last_month_profit_internal + last_month_profit_external
    
    profit_change = 0
    if last_month_profit > 0:
        profit_change = round(((current_month_profit - last_month_profit) / last_month_profit) * 100, 2)
    
    current_month_expenses = Expense.objects.filter(
        created_at__date__gte=first_day_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    recent_orders = []
    
    internal_recent = InternalOrder.objects.filter(
        status__in=['confirmed', 'indelivery', 'received']
    ).select_related('customer').order_by('-created_at')[:5]
    
    for order in internal_recent:
        recent_orders.append({
            'order_number': order.order_number,
            'customer': order.customer.full_name if order.customer else 'عميل',
            'city': order.customer.city if order.customer and order.customer.city else '-',
            'amount': order.sales_total,
            'status': order.status,
            'status_display': order.get_status_display()
        })
    
    external_recent = ExternalOrder.objects.filter(
        status__in=['confirmed', 'indeliver', 'received']
    ).select_related('customer').order_by('-created_at')[:5]
    
    for order in external_recent:
        recent_orders.append({
            'order_number': order.order_number,
            'customer': order.customer.full_name if order.customer else 'عميل',
            'city': order.customer.city if order.customer and order.customer.city else '-',
            'amount': order.lyd_sales_total,
            'status': order.status,
            'status_display': order.get_status_display()
        })
    
    recent_orders = sorted(recent_orders, key=lambda x: x['order_number'], reverse=True)[:5]
    
    low_stock_items = Inventory.objects.select_related('product').filter(
        quantity__lt=5
    ).order_by('quantity')[:5]
    
    low_stock = []
    for item in low_stock_items:
        low_stock.append({
            'product_name': item.product.name,
            'quantity': item.quantity
        })
    
    best_selling_data = defaultdict(int)
    
    internal_items = InternalOrderItem.objects.filter(
        order__status__in=['confirmed', 'indelivery', 'received']
    ).select_related('product')
    
    for item in internal_items:
        best_selling_data[item.product.name] += item.quantity
    
    external_items = ExternalOrderItem.objects.filter(
        order__status__in=['confirmed', 'indeliver', 'received']
    )
    
    for item in external_items:
        best_selling_data[item.product_name] += item.quantity
    
    sorted_products = sorted(
        best_selling_data.items(),
        key=lambda x: x[1],
        reverse=True
    )[:4]
    
    best_selling = []
    for name, quantity in sorted_products:
        best_selling.append({
            'name': name,
            'quantity': quantity
        })
    
    channel_data = Customer.objects.values('known_us_from').annotate(
        count=Count('id')
    ).order_by('-count')
    
    channel_names = {
        'facebook': 'فيسبوك',
        'instagram': 'إنستغرام',
        'tiktok': 'تيكتوك',
        'snapchat': 'سناب شات',
        'friend': 'صديق',
        'advertisement': 'إعلان',
        'other': 'أخرى'
    }
    
    total_customers = Customer.objects.count()
    
    sales_channels = []
    for item in channel_data:
        if item['known_us_from']:
            percentage = round((item['count'] / total_customers) * 100, 2) if total_customers > 0 else 0
            sales_channels.append({
                'name': channel_names.get(item['known_us_from'], item['known_us_from']),
                'percentage': percentage
            })
    
    expense_details = Expense.objects.filter(
        created_at__date__gte=first_day_month
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    expense_data = []
    for item in expense_details:
        expense_data.append({
            'name': item['category__name'] or 'أخرى',
            'amount': item['total'] or 0
        })
    
    thirty_days_ago = today - timedelta(days=30)
    daily_data = {}
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        daily_data[date.strftime('%Y-%m-%d')] = 0
    
    internal_daily = InternalOrder.objects.filter(
        created_at__date__gte=thirty_days_ago,
        created_at__date__lte=today,
        status__in=['confirmed', 'indelivery', 'received']
    ).values('created_at__date').annotate(total=Sum('sales_total'))
    
    for item in internal_daily:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        if date_str in daily_data:
            daily_data[date_str] += float(item['total'] or 0)
    
    external_daily = ExternalOrder.objects.filter(
        created_at__date__gte=thirty_days_ago,
        created_at__date__lte=today,
        status__in=['confirmed', 'indeliver', 'received']
    ).values('created_at__date').annotate(total=Sum('lyd_sales_total'))
    
    for item in external_daily:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        if date_str in daily_data:
            daily_data[date_str] += float(item['total'] or 0)
    
    sorted_dates = sorted(daily_data.keys())
    chart_labels = [d[5:10] for d in sorted_dates]
    chart_values = [daily_data[d] for d in sorted_dates]
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': current_month_sales,
        'total_profit': current_month_profit,
        'total_expenses': current_month_expenses,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'best_selling': best_selling,
        'sales_channels': sales_channels,
        'expense_data': expense_data,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'sales_change': sales_change,
        'profit_change': profit_change,
    }
    
    
    return render(request, 'home.html', context)


def get_best_selling_products():
    """الحصول على أفضل 4 منتجات مبيعاً"""
    from collections import defaultdict
    
    product_data = defaultdict(int)
    
    internal_items = InternalOrderItem.objects.filter(
        order__status__in=['confirmed', 'indelivery', 'received']
    ).select_related('product')
    
    for item in internal_items:
        product_data[item.product.name] += item.quantity
    
    external_items = ExternalOrderItem.objects.filter(
        order__status__in=['confirmed', 'indeliver', 'received']
    )
    
    for item in external_items:
        product_data[item.product_name] += item.quantity
    
    sorted_products = sorted(
        product_data.items(),
        key=lambda x: x[1],
        reverse=True
    )[:4]
    
    return [
        {
            'name': name,
            'quantity': quantity
        }
        for name, quantity in sorted_products
    ]


def get_daily_sales_chart():
    """الحصول على بيانات المبيعات اليومية لآخر 30 يوم"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    daily_data = {}
    
    # تهيئة كل الأيام
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        daily_data[date.strftime('%Y-%m-%d')] = 0
    
    # المبيعات الداخلية
    internal_sales = InternalOrder.objects.filter(
        created_at__date__gte=thirty_days_ago,
        created_at__date__lte=today,
        status__in=['confirmed', 'indelivery', 'received']
    ).values('created_at__date').annotate(total=Sum('sales_total'))
    
    for item in internal_sales:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        if date_str in daily_data:
            daily_data[date_str] += float(item['total'] or 0)
    
    # المبيعات الخارجية
    external_sales = ExternalOrder.objects.filter(
        created_at__date__gte=thirty_days_ago,
        created_at__date__lte=today,
        status__in=['confirmed', 'indeliver', 'received']
    ).values('created_at__date').annotate(total=Sum('lyd_sales_total'))
    
    for item in external_sales:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        if date_str in daily_data:
            daily_data[date_str] += float(item['total'] or 0)
    
    sorted_dates = sorted(daily_data.keys())
    
    return {
        'labels': [d[5:10] for d in sorted_dates],  # عرض اليوم والشهر فقط
        'values': [daily_data[d] for d in sorted_dates]
    }    

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user and user.is_active:
                login(request, user)
                return redirect('home')
  
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):

    logout(request)
    return redirect('user_login')


@login_required
def users_list(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    users = CustomUser.objects.all().order_by('username')
    return render(request, 'accounts/users_list.html', {'users': users})


@login_required
def user_create(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
    
            messages.success(request, f'تم إنشاء المستخدم {user.username} بنجاح')
            return redirect('users_list')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'إضافة مستخدم جديد'})


@login_required
def user_edit(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
          
            messages.success(request, 'تم تحديث بيانات المستخدم بنجاح')
            return redirect('users_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'تعديل المستخدم', 'user_obj': user})


@login_required
def user_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'غير مصرح لك بهذه العملية')
        return redirect('users_list')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    if user == request.user:
        messages.error(request, 'لا يمكنك حذف حسابك الخاص')
        return redirect('users_list')
    
    user.delete()
    messages.success(request, f'تم حذف المستخدم {user.get_full_name() or user.username} بنجاح')
    return redirect('users_list')

@login_required
def category_list(request):

    categories = Category.objects.all()
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'products/category_list.html', {'page_obj': page_obj})

@login_required
def category_add(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الفئة بنجاح')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'products/category_form.html', {'form': form, 'title': 'إضافة فئة'})

@login_required
def category_edit(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الفئة بنجاح')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'products/category_form.html', {'form': form, 'title': 'تعديل فئة'})

@login_required
def category_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'تم حذف الفئة بنجاح')
        return redirect('category_list')
    return render(request, 'products/category_confirm_delete.html', {'category': category})

@login_required
def product_list(request):

    products = Product.objects.select_related('category').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
    
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all().order_by('name')
    
    return render(request, 'products/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id
    })

@login_required
def product_add(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة المنتج بنجاح')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form, 'title': 'إضافة منتج'})

@login_required
def product_edit(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')    
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث المنتج بنجاح')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'title': 'تعديل منتج'})

@login_required
def product_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')    
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'تم حذف المنتج بنجاح')
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})


@login_required
def product_price_update(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')    
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids[]')
        update_type = request.POST.get('update_type')
        value = request.POST.get('value')
        
        if not product_ids:
            messages.error(request, 'يرجى اختيار منتج واحد على الأقل')
            return redirect('product_price_update')
        
        if not value:
            messages.error(request, 'يرجى إدخال القيمة')
            return redirect('product_price_update')
        
        try:
            value = Decimal(str(value))
        except:
            messages.error(request, 'القيمة المدخلة غير صحيحة')
            return redirect('product_price_update')
        
        if value <= 0:
            messages.error(request, 'القيمة يجب أن تكون أكبر من صفر')
            return redirect('product_price_update')
        
        with transaction.atomic():
            products = Product.objects.filter(id__in=product_ids)
            
            if update_type == 'fixed':
                for product in products:
                    product.lyd_sell_price = product.lyd_sell_price + value
                    product.save()
                messages.success(request, f'تم إضافة {value} دينار لسعر البيع لـ {products.count()} منتج')
            
            elif update_type == 'exchange_rate':
                updated_count = 0
                for product in products:
                    if product.usd_sell_price > 0:
                        product.lyd_sell_price = product.usd_sell_price * value
                        product.save()
                        updated_count += 1
                messages.success(request, f'تم تحديث سعر البيع بالدينار لـ {updated_count} منتج بسعر صرف {value}')
            
            else:
                messages.error(request, 'نوع التحديث غير صحيح')
                return redirect('product_price_update')
        
        return redirect('product_price_update')
    
    products = Product.objects.all().order_by('name')
    return render(request, 'products/product_price_update.html', {'products': products})

@login_required
def product_price_update_ajax(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        field = request.POST.get('field')
        value = request.POST.get('value')
        
        if not product_id or not field or not value:
            return JsonResponse({'error': 'بيانات غير مكتملة'}, status=400)
        
        try:
            product = get_object_or_404(Product, pk=product_id)
            value = Decimal(str(value))
            
            if field == 'lyd_sell_price':
                product.lyd_sell_price = value
                product.save()
                return JsonResponse({
                    'success': True,
                    'message': f'تم تحديث سعر المنتج {product.name}',
                    'new_value': float(product.lyd_sell_price)
                })
            elif field == 'usd_sell_price':
                product.usd_sell_price = value
                product.save()
                return JsonResponse({
                    'success': True,
                    'message': f'تم تحديث سعر المنتج {product.name}',
                    'new_value': float(product.usd_sell_price)
                })
            else:
                return JsonResponse({'error': 'حقل غير صحيح'}, status=400)
                
        except Product.DoesNotExist:
            return JsonResponse({'error': 'المنتج غير موجود'}, status=404)
        except:
            return JsonResponse({'error': 'القيمة غير صحيحة'}, status=400)
    
    return JsonResponse({'error': 'طريقة غير مسموحة'}, status=405)


@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            messages.success(request, 'تم إضافة العميل بنجاح')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'إضافة عميل'})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث العميل بنجاح')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'تعديل عميل'})

@login_required
def customer_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'تم حذف العميل بنجاح')
        return redirect('customer_list')
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})


@login_required
def customer_detail(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    customer = get_object_or_404(Customer, pk=pk)
    
    pending_orders = []
    
    internal_orders = customer.internalorder_set.filter(
        status__in=['confirmed', 'indelivery'],
        debt_amount__gt=0
    ).order_by('created_at')
    
    for order in internal_orders:
        pending_orders.append({
            'order': order,
            'type': 'internal',
            'type_display': 'داخلي',
            'type_class': 'bg-primary/10 text-primary'
        })
    
    external_orders = customer.externalorder_set.filter(
        status='confirmed',
        lyd_debt_amount__gt=0
    ).order_by('created_at')
    
    for order in external_orders:
        pending_orders.append({
            'order': order,
            'type': 'external',
            'type_display': 'خارجي',
            'type_class': 'bg-warning/10 text-warning'
        })
    
    pending_orders = sorted(pending_orders, key=lambda x: x['order'].created_at)
    
    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'pending_orders': pending_orders,
    })
@login_required
def payment_add(request, customer_pk):
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerPaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.customer = customer
                payment.created_by = request.user
                payment.save()
                
                pending_internal_orders = InternalOrder.objects.filter(
                    customer=customer,
                    status__in=['confirmed', 'indelivery'],
                    debt_amount__gt=0
                ).order_by('created_at')
                
                remaining_amount = amount
                
                for order in pending_internal_orders:
                    if remaining_amount <= 0:
                        break
                    
                    if order.debt_amount >= remaining_amount:
                        order.paid_amount += remaining_amount
                        order.debt_amount -= remaining_amount
                        remaining_amount = 0
                    else:
                        remaining_amount -= order.debt_amount
                        order.paid_amount += order.debt_amount
                        order.debt_amount = 0
                    
                    order.save()
                
                if remaining_amount > 0:
                    pending_external_orders = ExternalOrder.objects.filter(
                        customer=customer,
                        status__in=['confirmed', 'indeliver'],
                        lyd_debt_amount__gt=0
                    ).order_by('created_at')
                    
                    for order in pending_external_orders:
                        if remaining_amount <= 0:
                            break
                        
                        if order.lyd_debt_amount >= remaining_amount:
                            order.lyd_paid_amount += remaining_amount
                            order.lyd_debt_amount -= remaining_amount
                            remaining_amount = 0
                        else:
                            remaining_amount -= order.lyd_debt_amount
                            order.lyd_paid_amount += order.lyd_debt_amount
                            order.lyd_debt_amount = 0
                        
                        order.save()
                
                internal_debt = InternalOrder.objects.filter(
                    customer=customer,
                    status__in=['confirmed', 'indelivery']
                ).aggregate(total_debt=Sum('debt_amount'))['total_debt'] or Decimal('0')
                
                external_debt = ExternalOrder.objects.filter(
                    customer=customer,
                    status__in=['confirmed', 'indeliver']
                ).aggregate(total_debt=Sum('lyd_debt_amount'))['total_debt'] or Decimal('0')
                
                customer.debt_balance = internal_debt + external_debt
                customer.save()
                
                if remaining_amount > 0:
                    messages.warning(request, f'تم تسجيل الدفعة ولكن بقي مبلغ {remaining_amount} لم يتم توزيعه على طلبات (رصيد دائن للعميل)')
                else:
                    messages.success(request, 'تم تسجيل الدفعة بنجاح')
                    
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerPaymentForm(initial={'payment_date': timezone.now()})
    
    internal_debt = InternalOrder.objects.filter(
        customer=customer,
        status__in=['confirmed', 'indelivery']
    ).aggregate(total_debt=Sum('debt_amount'))['total_debt'] or Decimal('0')
    
    external_debt = ExternalOrder.objects.filter(
        customer=customer,
        status__in=['confirmed', 'indeliver']
    ).aggregate(total_debt=Sum('lyd_debt_amount'))['total_debt'] or Decimal('0')
    
    total_debt = internal_debt + external_debt
    
    return render(request, 'customers/payment_form.html', {
        'form': form,
        'customer': customer,
        'total_debt': total_debt,
        'internal_debt': internal_debt,
        'external_debt': external_debt,
        'title': 'تسديد دين'
    })

@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(CustomerPayment, pk=pk)
    customer_pk = payment.customer.pk
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'تم حذف الدفعة بنجاح')
        return redirect('customer_detail', pk=customer_pk)
    return render(request, 'customers/payment_confirm_delete.html', {'payment': payment})

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    
    search_query = request.GET.get('search', '')
    filter_debt = request.GET.get('filter_debt', '')
    
    if search_query:
        customers = customers.filter(
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    if filter_debt == 'has_debt':
        customers = customers.filter(debt_balance__gt=0)
    elif filter_debt == 'no_debt':
        customers = customers.filter(debt_balance=0)
    
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'customers/customer_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_debt': filter_debt
    })

@login_required
def payment_list(request):
    payments = CustomerPayment.objects.select_related('customer', 'created_by').all().order_by('-payment_date')
    
    customer_id = request.GET.get('customer', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if customer_id:
        payments = payments.filter(customer_id=customer_id)
    
    if date_from:
        try:
            from datetime import datetime
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    customers = Customer.objects.all().order_by('full_name')
    
    return render(request, 'customers/payment_list.html', {
        'page_obj': page_obj,
        'customers': customers,
        'selected_customer': customer_id,
        'date_from': date_from,
        'date_to': date_to
    })
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'suppliers/supplier_list.html', {'page_obj': page_obj})

@login_required
def supplier_add(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة المورد بنجاح')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'إضافة مورد'})

@login_required
def supplier_edit(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')    
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث المورد بنجاح')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'تعديل مورد'})

@login_required
def supplier_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'تم حذف المورد بنجاح')
        return redirect('supplier_list')
    return render(request, 'suppliers/supplier_confirm_delete.html', {'supplier': supplier})

@login_required
def supplier_detail(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    supplier = get_object_or_404(Supplier, pk=pk)
    payments = supplier.payments.all().order_by('-payment_date')
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'payments': payments,
        'total_paid': total_paid,
    })
@login_required
def supplier_payment_add(request, supplier_pk):
    supplier = get_object_or_404(Supplier, pk=supplier_pk)
    
    if request.method == 'POST':
        form = SupplierPaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.supplier = supplier
                payment.created_by = request.user
                payment.save()
                
                pending_invoices = PurchaseInvoice.objects.filter(
                    supplier=supplier,
                    status='confirmed',
                    debt_amount__gt=0
                ).order_by('created_at')
                
                remaining_amount = amount
                
                for invoice in pending_invoices:
                    if remaining_amount <= 0:
                        break
                    
                    if invoice.debt_amount >= remaining_amount:
                        invoice.paid_amount += remaining_amount
                        invoice.debt_amount -= remaining_amount
                        remaining_amount = 0
                    else:
                        remaining_amount -= invoice.debt_amount
                        invoice.paid_amount += invoice.debt_amount
                        invoice.debt_amount = 0
                    
                    invoice.save()
                
                supplier.update_debt_balance()
                
                if remaining_amount > 0:
                    messages.warning(request, f'تم تسجيل الدفعة ولكن بقي مبلغ {remaining_amount} لم يتم توزيعه على فواتير (رصيد دائن للمورد)')
                else:
                    messages.success(request, 'تم تسجيل الدفعة بنجاح')
                    
            return redirect('supplier_detail', pk=supplier.pk)
    else:
        form = SupplierPaymentForm(initial={'payment_date': timezone.now().date()})
    
    total_debt = PurchaseInvoice.objects.filter(
        supplier=supplier,
        status='confirmed'
    ).aggregate(total_debt=Sum('debt_amount'))['total_debt'] or 0
    
    return render(request, 'suppliers/supplier_payment_form.html', {
        'form': form,
        'supplier': supplier,
        'total_debt': total_debt,
        'title': 'سداد مورد'
    })

@login_required
def supplier_payment_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    payment = get_object_or_404(SupplierPayment, pk=pk)
    supplier_pk = payment.supplier.pk
    if request.method == 'POST':
        payment.delete()
        supplier = get_object_or_404(Supplier, pk=supplier_pk)
        supplier.update_debt_balance()
        messages.success(request, 'تم حذف الدفعة بنجاح')
        return redirect('supplier_detail', pk=supplier_pk)
    return render(request, 'suppliers/supplier_payment_confirm_delete.html', {'payment': payment})

@login_required
def supplier_payment_list(request):
    payments = SupplierPayment.objects.select_related('supplier', 'created_by').all().order_by('-payment_date')
    
    supplier_id = request.GET.get('supplier', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment_method = request.GET.get('payment_method', '')
    
    if supplier_id:
        payments = payments.filter(supplier_id=supplier_id)
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__lte=date_to_parsed)
        except ValueError:
            pass
    
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    suppliers = Supplier.objects.all().order_by('name')
    payment_methods = SupplierPayment.PAYMENT_METHODS
    
    return render(request, 'suppliers/supplier_payment_list.html', {
        'page_obj': page_obj,
        'suppliers': suppliers,
        'payment_methods': payment_methods,
        'selected_supplier': supplier_id,
        'selected_method': payment_method,
        'date_from': date_from,
        'date_to': date_to
    })

@login_required
def expense_category_list(request):
    categories = ExpenseCategory.objects.all()
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/expense_category_list.html', {'page_obj': page_obj})

@login_required
def expense_category_add(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة فئة المصروف بنجاح')
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm()
    return render(request, 'dashboard/expense_category_form.html', {'form': form, 'title': 'إضافة فئة مصروف'})

@login_required
def expense_category_edit(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    category = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث فئة المصروف بنجاح')
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm(instance=category)
    return render(request, 'dashboard/expense_category_form.html', {'form': form, 'title': 'تعديل فئة مصروف'})

@login_required
def expense_category_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    category = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'تم حذف فئة المصروف بنجاح')
        return redirect('expense_category_list')
    return render(request, 'dashboard/expense_category_confirm_delete.html', {'category': category})

@login_required
def expense_list(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    expenses = Expense.objects.select_related('category', 'created_by').all()
    
    category_id = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    if search_query:
        expenses = expenses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            expenses = expenses.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            expenses = expenses.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = ExpenseCategory.objects.all().order_by('name')
    
    return render(request, 'dashboard/expense_list.html', {
        'page_obj': page_obj,
        'total_expenses': total_expenses,
        'categories': categories,
        'selected_category': category_id,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query
    })

@login_required
def expense_add(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'تم إضافة المصروف بنجاح')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'dashboard/expense_form.html', {'form': form, 'title': 'إضافة مصروف'})

@login_required
def expense_edit(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث المصروف بنجاح')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'dashboard/expense_form.html', {'form': form, 'title': 'تعديل مصروف'})

@login_required
def expense_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'تم حذف المصروف بنجاح')
        return redirect('expense_list')
    return render(request, 'dashboard/expense_confirm_delete.html', {'expense': expense})

@login_required
def expense_detail(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    expense = get_object_or_404(Expense, pk=pk)
    return render(request, 'dashboard/expense_detail.html', {'expense': expense})

@login_required
def inventory_list(request):
    product_id = request.GET.get('product')
    inventory_items = Inventory.objects.select_related('product').all()
  
    if product_id:
        inventory_items  = inventory_items.filter(product_id=product_id)
    
    
    for item in inventory_items:
        item.total_buy_value = item.quantity * item.lyd_total_cost
        item.total_sell_value = item.quantity * item.lyd_sell_price
        item.profit_margin = item.lyd_sell_price - item.lyd_total_cost
        item.status_data = item.get_movement_status()
    
    total_buy_value = inventory_items.aggregate(
        total=Sum(F('quantity') * F('lyd_total_cost'))
    )['total'] or 0
    
    total_sell_value = inventory_items.aggregate(
        total=Sum(F('quantity') * F('lyd_sell_price'))
    )['total'] or 0
    
    total_profit = total_sell_value - total_buy_value
    
    paginator = Paginator(inventory_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    products = Product.objects.all().order_by('name')
    
    
    return render(request, 'dashboard/inventory_list.html', {
        'page_obj': page_obj,
        'total_buy_value': total_buy_value,
        'total_sell_value': total_sell_value,
        'total_profit': total_profit,
        'selected_product': product_id,
        'products': products,
    })

@login_required
def inventory_damage(request, product_pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    product = get_object_or_404(Product, pk=product_pk)
    inventory = get_object_or_404(Inventory, product=product)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        if quantity <= 0:
            messages.error(request, 'يجب أن تكون الكمية أكبر من صفر')
            return redirect('inventory_list')
        
        if quantity > inventory.quantity:
            messages.error(request, f'الكمية المطلوبة ({quantity}) أكبر من الكمية المتوفرة ({inventory.quantity})')
            return redirect('inventory_list')
        
        movement = InventoryMovement.objects.create(
            product=product,
            movement_type='damage',
            quantity=-quantity,
            notes=notes or f'اتلاف {quantity} وحدة من {product.name}',
            created_by=request.user
        )
        
        inventory.quantity -= quantity
        inventory.save()
        
        messages.success(request, f'تم اتلاف {quantity} وحدة من {product.name} بنجاح')
        return redirect('inventory_list')
    
    return render(request, 'dashboard/inventory_damage.html', {
        'product': product,
        'inventory': inventory,
        'title': 'اتلاف منتج'
    })

@login_required
def inventory_gift(request, product_pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    product = get_object_or_404(Product, pk=product_pk)
    inventory = get_object_or_404(Inventory, product=product)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        if quantity <= 0:
            messages.error(request, 'يجب أن تكون الكمية أكبر من صفر')
            return redirect('inventory_list')
        
        if quantity > inventory.quantity:
            messages.error(request, f'الكمية المطلوبة ({quantity}) أكبر من الكمية المتوفرة ({inventory.quantity})')
            return redirect('inventory_list')
        
        movement = InventoryMovement.objects.create(
            product=product,
            movement_type='gift',
            quantity=-quantity,
            notes=notes or f'هدية {quantity} وحدة من {product.name}',
            created_by=request.user
        )
        
        inventory.quantity -= quantity
        inventory.save()
        
        messages.success(request, f'تم تسجيل {quantity} وحدة كهدية من {product.name} بنجاح')
        return redirect('inventory_list')
    
    return render(request, 'dashboard/inventory_gift.html', {
        'product': product,
        'inventory': inventory,
        'title': 'تسجيل هدية'
    })

@login_required
def inventory_stock_adjustment(request, product_pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    product = get_object_or_404(Product, pk=product_pk)
    inventory = get_object_or_404(Inventory, product=product)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        adjustment_type = request.POST.get('adjustment_type')
        notes = request.POST.get('notes', '')
        
        if quantity <= 0:
            messages.error(request, 'يجب أن تكون الكمية أكبر من صفر')
            return redirect('inventory_list')
        
        if adjustment_type == 'stock_addition':
            movement_type = 'stock_addition'
            movement_quantity = quantity
            inventory.quantity += quantity
            message = f'تم إضافة {quantity} وحدة إلى مخزون {product.name} بنجاح'
        elif adjustment_type == 'stock_deduction':
            if quantity > inventory.quantity:
                messages.error(request, f'الكمية المطلوبة ({quantity}) أكبر من الكمية المتوفرة ({inventory.quantity})')
                return redirect('inventory_list')
            movement_type = 'stock_deduction'
            movement_quantity = -quantity
            inventory.quantity -= quantity
            message = f'تم خصم {quantity} وحدة من مخزون {product.name} بنجاح'
        else:
            messages.error(request, 'نوع الجرد غير صحيح')
            return redirect('inventory_list')
        
        movement = InventoryMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=movement_quantity,
            notes=notes or f'جرد {quantity} وحدة من {product.name}',
            created_by=request.user
        )
        
        inventory.save()
        
        messages.success(request, message)
        return redirect('inventory_list')
    
    return render(request, 'dashboard/inventory_stock_adjustment.html', {
        'product': product,
        'inventory': inventory,
        'title': 'جرد المخزون'
    })

@login_required
def inventory_movement_list(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    movements = InventoryMovement.objects.select_related('product', 'created_by').all().order_by('-created_at')
    
    movement_type = request.GET.get('movement_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    product_id = request.GET.get('product')
    
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    if date_from:
        movements = movements.filter(created_at__date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        movements = movements.filter(created_at__date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
    if product_id:
        movements = movements.filter(product_id=product_id)
    
    paginator = Paginator(movements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    movement_types = InventoryMovement.MOVEMENT_TYPES
    products = Product.objects.all().order_by('name')
    
    return render(request, 'dashboard/inventory_movement_list.html', {
        'page_obj': page_obj,
        'movement_types': movement_types,
        'selected_type': movement_type,
        'date_from': date_from,
        'date_to': date_to,
        'selected_product': product_id,
        'products': products,
    })

@login_required
def inventory_movement_delete(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    movement = get_object_or_404(InventoryMovement, pk=pk)
    if request.method == 'POST':
        movement.delete()
        messages.success(request, 'تم حذف الحركة بنجاح')
        return redirect('inventory_movement_list')
    return render(request, 'dashboard/inventory_movement_confirm_delete.html', {'movement': movement})

@login_required
def purchase_invoice_list(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    invoices = PurchaseInvoice.objects.select_related('supplier', 'created_by').all().order_by('-created_at')
    
    search_query = request.GET.get('search', '')
    supplier_id = request.GET.get('supplier', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    receive_date_from = request.GET.get('receive_date_from', '')
    receive_date_to = request.GET.get('receive_date_to', '')
    
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    if supplier_id:
        invoices = invoices.filter(supplier_id=supplier_id)
    
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            invoices = invoices.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            invoices = invoices.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    if receive_date_from:
        try:
            receive_date_from_parsed = datetime.strptime(receive_date_from, '%Y-%m-%d').date()
            invoices = invoices.filter(receive_date__date__gte=receive_date_from_parsed)
        except ValueError:
            pass
    
    if receive_date_to:
        try:
            receive_date_to_parsed = datetime.strptime(receive_date_to, '%Y-%m-%d').date()
            invoices = invoices.filter(receive_date__date__lte=receive_date_to_parsed)
        except ValueError:
            pass
    
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    suppliers = Supplier.objects.all().order_by('name')
    status_choices = PurchaseInvoice.STATUS_CHOICES
    
    return render(request, 'dashboard/purchase_invoice_list.html', {
        'page_obj': page_obj,
        'suppliers': suppliers,
        'status_choices': status_choices,
        'search_query': search_query,
        'selected_supplier': supplier_id,
        'selected_status': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'receive_date_from': receive_date_from,
        'receive_date_to': receive_date_to,
    })

@login_required
def purchase_invoice_add(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        subtotal = float(request.POST.get('subtotal', 0))
        discount = float(request.POST.get('discount', 0))
        shipping_cost = float(request.POST.get('shipping_cost', 0))
        exchange_rate = float(request.POST.get('exchange_rate', 1))
        paid_amount = float(request.POST.get('paid_amount', 0))
        receive_date = request.POST.get('receive_date')
        notes = request.POST.get('notes', '')
        status = request.POST.get('status', 'draft')
        
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_usd_prices = request.POST.getlist('unit_usd_prices[]')
        unit_lyd_prices = request.POST.getlist('unit_lyd_prices[]')
        
        if not supplier_id:
            messages.error(request, 'يرجى اختيار المورد')
            return redirect('purchase_invoice_add')
        
        if not product_ids:
            messages.error(request, 'يرجى إضافة منتج واحد على الأقل')
            return redirect('purchase_invoice_add')
        
        with transaction.atomic():
            total_quantity = sum(int(q) for q in quantities)
            shipping_per_unit_usd = shipping_cost / total_quantity if total_quantity > 0 else 0
            
            invoice = PurchaseInvoice.objects.create(
                supplier_id=supplier_id,
                subtotal=subtotal,
                discount=discount,
                total=subtotal - discount + shipping_cost,
                paid_amount=paid_amount,
                debt_amount=subtotal - discount + shipping_cost - paid_amount,
                shipping_cost=shipping_cost,
                exchange_rate=exchange_rate,
                receive_date=receive_date,
                notes=notes,
                status=status,
                created_by=request.user
            )
            
            for i in range(len(product_ids)):
                product_id = product_ids[i]
                quantity = int(quantities[i])
                unit_usd = float(unit_usd_prices[i]) if unit_usd_prices[i] else 0
                unit_lyd = float(unit_lyd_prices[i]) if unit_lyd_prices[i] else 0
                
                if unit_lyd > 0 and exchange_rate > 0:
                    unit_usd = unit_lyd / exchange_rate
                elif unit_usd > 0:
                    unit_lyd = unit_usd * exchange_rate
                
                unit_shipping_usd = shipping_per_unit_usd
                unit_shipping_lyd = unit_shipping_usd * exchange_rate
                
                total_usd_price = (unit_usd * quantity) + (unit_shipping_usd * quantity)
                total_lyd_price = (unit_lyd * quantity) + (unit_shipping_lyd * quantity)
                
                PurchaseInvoiceItem.objects.create(
                    invoice=invoice,
                    product_id=product_id,
                    quantity=quantity,
                    unit_lyd=unit_lyd,
                    unit_usd=unit_usd,
                    unit_shipping_cost_lyd=unit_shipping_lyd,
                    unit_shipping_cost_usd=unit_shipping_usd,
                    total_lyd_price=total_lyd_price,
                    total_usd_price=total_usd_price,
                    exchange_rate=exchange_rate
                )
            
            if status == 'confirmed':
                confirm_invoice(invoice)
            
            messages.success(request, f'تم إنشاء الفاتورة رقم {invoice.invoice_number} بنجاح')
            return redirect('purchase_invoice_list')
    
    suppliers = Supplier.objects.all().order_by('name')
    products = Product.objects.all().order_by('name')
    return render(request, 'dashboard/purchase_invoice_add.html', {
        'suppliers': suppliers,
        'products': products
    })

@login_required
def purchase_invoice_edit(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    invoice = get_object_or_404(PurchaseInvoice, pk=pk)
    if invoice.status != 'draft':
        messages.error(request, 'لا يمكن تعديل فاتورة غير مسودة')
        return redirect('purchase_invoice_detail', pk=pk)
    
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        subtotal = float(request.POST.get('subtotal', 0))
        discount = float(request.POST.get('discount', 0))
        shipping_cost = float(request.POST.get('shipping_cost', 0))
        exchange_rate = float(request.POST.get('exchange_rate', 1))
        paid_amount = float(request.POST.get('paid_amount', 0))
        receive_date = request.POST.get('receive_date')
        notes = request.POST.get('notes', '')
        status = request.POST.get('status', 'draft')
        
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_usd_prices = request.POST.getlist('unit_usd_prices[]')
        unit_lyd_prices = request.POST.getlist('unit_lyd_prices[]')
        
        if not supplier_id:
            messages.error(request, 'يرجى اختيار المورد')
            return redirect('purchase_invoice_edit', pk=pk)
        
        if not product_ids:
            messages.error(request, 'يرجى إضافة منتج واحد على الأقل')
            return redirect('purchase_invoice_edit', pk=pk)
        
        with transaction.atomic():
            total_quantity = sum(int(q) for q in quantities)
            shipping_per_unit_usd = shipping_cost / total_quantity if total_quantity > 0 else 0
            
            invoice.supplier_id = supplier_id
            invoice.subtotal = subtotal
            invoice.discount = discount
            invoice.total = subtotal - discount + shipping_cost
            invoice.paid_amount = paid_amount
            invoice.debt_amount = subtotal - discount + shipping_cost - paid_amount
            invoice.shipping_cost = shipping_cost
            invoice.exchange_rate = exchange_rate
            invoice.receive_date = receive_date
            invoice.notes = notes
            invoice.status = status
            invoice.save()
            
            invoice.items.all().delete()
            
            for i in range(len(product_ids)):
                product_id = product_ids[i]
                quantity = int(quantities[i])
                unit_usd = float(unit_usd_prices[i]) if unit_usd_prices[i] else 0
                unit_lyd = float(unit_lyd_prices[i]) if unit_lyd_prices[i] else 0
                
                if unit_lyd > 0 and exchange_rate > 0:
                    unit_usd = unit_lyd / exchange_rate
                elif unit_usd > 0:
                    unit_lyd = unit_usd * exchange_rate
                
                unit_shipping_usd = shipping_per_unit_usd
                unit_shipping_lyd = unit_shipping_usd * exchange_rate
                
                total_usd_price = (unit_usd * quantity) + (unit_shipping_usd * quantity)
                total_lyd_price = (unit_lyd * quantity) + (unit_shipping_lyd * quantity)
                
                PurchaseInvoiceItem.objects.create(
                    invoice=invoice,
                    product_id=product_id,
                    quantity=quantity,
                    unit_lyd=unit_lyd,
                    unit_usd=unit_usd,
                    unit_shipping_cost_lyd=unit_shipping_lyd,
                    unit_shipping_cost_usd=unit_shipping_usd,
                    total_lyd_price=total_lyd_price,
                    total_usd_price=total_usd_price,
                    exchange_rate=exchange_rate
                )
            
            if status == 'confirmed':
                confirm_invoice(invoice)
            elif status == 'cancelled':
                invoice.debt_amount = 0
                invoice.save()
            
            messages.success(request, f'تم تحديث الفاتورة رقم {invoice.invoice_number} بنجاح')
            return redirect('purchase_invoice_list')
    
    suppliers = Supplier.objects.all().order_by('name')
    products = Product.objects.all().order_by('name')
    return render(request, 'dashboard/purchase_invoice_edit.html', {
        'invoice': invoice,
        'suppliers': suppliers,
        'products': products
    })

@login_required
def purchase_invoice_detail(request, pk):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    invoice = get_object_or_404(PurchaseInvoice, pk=pk)
    return render(request, 'dashboard/purchase_invoice_detail.html', {'invoice': invoice})

@login_required
def purchase_invoice_confirm(request, pk):
    invoice = get_object_or_404(PurchaseInvoice, pk=pk)
    if invoice.status != 'draft':
        messages.error(request, 'لا يمكن تأكيد فاتورة غير مسودة')
        return redirect('purchase_invoice_detail', pk=pk)
    
    confirm_invoice(invoice)
    messages.success(request, f'تم تأكيد الفاتورة رقم {invoice.invoice_number} بنجاح')
    return redirect('purchase_invoice_detail', pk=pk)

@login_required
def purchase_invoice_cancel(request, pk):
    invoice = get_object_or_404(PurchaseInvoice, pk=pk)
    if invoice.status == 'confirmed':
        with transaction.atomic():
            for item in invoice.items.all():
                inventory = Inventory.objects.filter(product=item.product).first()
                if inventory:
                    inventory.quantity -= item.quantity
                    inventory.save()
                    
                    InventoryMovement.objects.create(
                        product=item.product,
                        movement_type='returned',
                        quantity=-item.quantity,
                        notes=f'الغاء فاتورة شراء {invoice.invoice_number}',
                        created_by=request.user
                    )
            
            invoice.supplier.update_debt_balance()
    
    invoice.status = 'cancelled'
    invoice.debt_amount = 0
    invoice.save()
    messages.success(request, f'تم الغاء الفاتورة رقم {invoice.invoice_number} بنجاح')
    return redirect('purchase_invoice_list')

@login_required
def purchase_invoice_delete(request, pk):
    invoice = get_object_or_404(PurchaseInvoice, pk=pk)
    if invoice.status == 'confirmed':
        messages.error(request, 'لا يمكن حذف فاتورة مؤكدة')
        return redirect('purchase_invoice_detail', pk=pk)
    
    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'تم حذف الفاتورة رقم {invoice_number} بنجاح')
        return redirect('purchase_invoice_list')
    
    return render(request, 'dashboard/purchase_invoice_confirm_delete.html', {'invoice': invoice})

def confirm_invoice(invoice):
    with transaction.atomic():
        for item in invoice.items.all():
            inventory, created = Inventory.objects.get_or_create(product=item.product)
            
            if created:
                inventory.quantity = item.quantity
                inventory.lyd_buy_coast_price = item.unit_lyd
                inventory.lyd_shipping_cost = item.unit_shipping_cost_lyd
                inventory.lyd_total_cost = item.unit_lyd + item.unit_shipping_cost_lyd
                inventory.usd_buy_coast_price = item.unit_usd
                inventory.usd_shipping_cost = item.unit_shipping_cost_usd
                inventory.usd_total_cost = item.unit_usd + item.unit_shipping_cost_usd
                inventory.exchange_rate = item.exchange_rate
            else:
                avg_lyd_cost = ((inventory.quantity * inventory.lyd_total_cost) + (item.quantity * (item.unit_lyd + item.unit_shipping_cost_lyd))) / (inventory.quantity + item.quantity)
                avg_usd_cost = ((inventory.quantity * inventory.usd_total_cost) + (item.quantity * (item.unit_usd + item.unit_shipping_cost_usd))) / (inventory.quantity + item.quantity)
                avg_shipping_lyd = ((inventory.quantity * inventory.lyd_shipping_cost) + (item.quantity * item.unit_shipping_cost_lyd)) / (inventory.quantity + item.quantity)
                avg_shipping_usd = ((inventory.quantity * inventory.usd_shipping_cost) + (item.quantity * item.unit_shipping_cost_usd)) / (inventory.quantity + item.quantity)
                
                inventory.quantity += item.quantity
                inventory.lyd_total_cost = avg_lyd_cost
                inventory.usd_total_cost = avg_usd_cost
                inventory.lyd_shipping_cost = avg_shipping_lyd
                inventory.usd_shipping_cost = avg_shipping_usd
                inventory.exchange_rate = item.exchange_rate
            
            inventory.save()
            
            InventoryMovement.objects.create(
                product=item.product,
                movement_type='purchase',
                quantity=item.quantity,
                notes=f'فاتورة شراء {invoice.invoice_number}',
                created_by=invoice.created_by
            )
        
        invoice.supplier.update_debt_balance()
        invoice.status = 'confirmed'
        invoice.save()
@login_required
def get_product_details(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    inventory = Inventory.objects.filter(product=product).first()
    data = {
        'product_name': product.name,
        'has_inventory': inventory is not None
    }
    return JsonResponse(data)




@login_required
def internal_order_list(request):
    orders = InternalOrder.objects.select_related('customer').all().order_by('-created_at')
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    debt_filter = request.GET.get('debt_filter', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__full_name__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if debt_filter == 'has_debt':
        orders = orders.filter(debt_amount__gt=0)
    elif debt_filter == 'no_debt':
        orders = orders.filter(debt_amount=0)
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    status_choices = InternalOrder.STATUS_CHOICES
    
    return render(request, 'orders/internal_order_list.html', {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'search_query': search_query,
        'selected_status': status_filter,
        'selected_debt': debt_filter,
        'date_from': date_from,
        'date_to': date_to
    })

@login_required
def internal_order_add(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        subtotal = Decimal(request.POST.get('subtotal', 0))
        discount = Decimal(request.POST.get('discount', 0))
        paid_amount = Decimal(request.POST.get('paid_amount', 0))
        delivery_address = request.POST.get('delivery_address', '')
        status = request.POST.get('status', 'draft')
        
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')
        unit_discounts = request.POST.getlist('unit_discounts[]')
        
        if not customer_id:
            messages.error(request, 'يرجى اختيار العميل')
            return redirect('internal_order_add')
        
        if not product_ids:
            messages.error(request, 'يرجى إضافة منتج واحد على الأقل')
            return redirect('internal_order_add')
        
        with transaction.atomic():
            sales_total = subtotal - discount
            debt_amount = sales_total - paid_amount
            if debt_amount < 0:
                debt_amount = Decimal('0')
            
            order = InternalOrder.objects.create(
                customer_id=customer_id,
                subtotal=subtotal,
                discount=discount,
                sales_total=sales_total,
                paid_amount=paid_amount,
                debt_amount=debt_amount,
                delivery_address=delivery_address,
                status=status,
                total_profit=Decimal('0')
            )
            
            total_profit = Decimal('0')
            
            for i in range(len(product_ids)):
                product_id = product_ids[i]
                quantity = int(quantities[i])
                unit_price = Decimal(unit_prices[i]) if unit_prices[i] else Decimal('0')
                unit_discount = Decimal(unit_discounts[i]) if unit_discounts[i] else Decimal('0')
                
                inventory = Inventory.objects.filter(product_id=product_id).first()
                unit_cost = inventory.lyd_total_cost if inventory else Decimal('0')
                unit_profit = unit_price - unit_discount - unit_cost
                total_price = (unit_price - unit_discount) * quantity
                item_total_profit = unit_profit * quantity
                total_profit += item_total_profit
                
                InternalOrderItem.objects.create(
                    order=order,
                    product_id=product_id,
                    quantity=quantity,
                    unit_discount=unit_discount,
                    unit_price=unit_price,
                    total_price=total_price,
                    unit_profit=unit_profit,
                    total_profit=item_total_profit
                )
            
            order.total_profit = total_profit
            order.save()
            
            if status == 'confirmed':
                confirm_internal_order(order)
            
            messages.success(request, f'تم إنشاء الطلبية رقم {order.order_number} بنجاح')
            return redirect('internal_order_list')
    
    customers = Customer.objects.all().order_by('full_name')
    products = Product.objects.all().order_by('name')
    return render(request, 'orders/internal_order_add.html', {
        'customers': customers,
        'products': products
    })

@login_required
def internal_order_edit(request, pk):
    order = get_object_or_404(InternalOrder, pk=pk)
    if order.status not in ['draft', 'cancelled']:
        messages.error(request, 'لا يمكن تعديل طلبية غير مسودة أو ملغاة')
        return redirect('internal_order_detail', pk=pk)
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        subtotal = Decimal(request.POST.get('subtotal', 0))
        discount = Decimal(request.POST.get('discount', 0))
        paid_amount = Decimal(request.POST.get('paid_amount', 0))
        delivery_address = request.POST.get('delivery_address', '')
        status = request.POST.get('status', 'draft')
        
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')
        unit_discounts = request.POST.getlist('unit_discounts[]')
        
        if not customer_id:
            messages.error(request, 'يرجى اختيار العميل')
            return redirect('internal_order_edit', pk=pk)
        
        if not product_ids:
            messages.error(request, 'يرجى إضافة منتج واحد على الأقل')
            return redirect('internal_order_edit', pk=pk)
        
        with transaction.atomic():
            sales_total = subtotal - discount
            debt_amount = sales_total - paid_amount
            if debt_amount < 0:
                debt_amount = Decimal('0')
            
            order.customer = Customer.objects.get(id=customer_id)
            order.subtotal = subtotal
            order.discount = discount
            order.sales_total = sales_total
            order.paid_amount = paid_amount
            order.debt_amount = debt_amount
            order.delivery_address = delivery_address
            order.status = status
            order.save()
            
            order.items.all().delete()
            
            total_profit = Decimal('0')
            
            for i in range(len(product_ids)):
                product_id = product_ids[i]
                quantity = int(quantities[i])
                unit_price = Decimal(unit_prices[i]) if unit_prices[i] else Decimal('0')
                unit_discount = Decimal(unit_discounts[i]) if unit_discounts[i] else Decimal('0')
                
                inventory = Inventory.objects.filter(product_id=product_id).first()
                unit_cost = inventory.lyd_total_cost if inventory else Decimal('0')
                unit_profit = unit_price - unit_discount - unit_cost
                total_price = (unit_price - unit_discount) * quantity
                item_total_profit = unit_profit * quantity
                total_profit += item_total_profit
                
                InternalOrderItem.objects.create(
                    order=order,
                    product_id=product_id,
                    quantity=quantity,
                    unit_discount=unit_discount,
                    unit_price=unit_price,
                    total_price=total_price,
                    unit_profit=unit_profit,
                    total_profit=item_total_profit
                )
            
            order.total_profit = total_profit
            order.save()
            
            if status == 'confirmed':
                confirm_internal_order(order)
            elif status == 'cancelled':
                order.debt_amount = Decimal('0')
                order.save()
            
            messages.success(request, f'تم تحديث الطلبية رقم {order.order_number} بنجاح')
            return redirect('internal_order_list')
    
    customers = Customer.objects.all().order_by('full_name')
    products = Product.objects.all().order_by('name')
    return render(request, 'orders/internal_order_edit.html', {
        'order': order,
        'customers': customers,
        'products': products
    })

@login_required
def internal_order_detail(request, pk):
    order = get_object_or_404(InternalOrder, pk=pk)
    return render(request, 'orders/internal_order_detail.html', {'order': order})

@login_required
def internal_order_confirm(request, pk):
    order = get_object_or_404(InternalOrder, pk=pk)
    if order.status != 'draft':
        messages.error(request, 'لا يمكن تأكيد طلبية غير مسودة')
        return redirect('internal_order_detail', pk=pk)
    with transaction.atomic():
        for item in order.items.all():
            inventory = Inventory.objects.filter(product=item.product).first()
            if not inventory or inventory.quantity < item.quantity:
                raise ValueError(f'الكمية غير متوفرة للمنتج {item.product.name}')

        order.status = 'confirmed'
        order.save()
    if order.customer:
        customer=order.customer
        customer.debt_balance += order.debt_amount
        customer.save()
    messages.success(request, f'تم تأكيد الطلبية رقم {order.order_number} بنجاح')
    return redirect('internal_order_list')

@login_required
def internal_order_deliver(request, pk):
    order = get_object_or_404(InternalOrder, pk=pk)
    if order.status != 'confirmed':
        messages.error(request, 'لا يمكن شحن طلبية غير مؤكدة')
        return redirect('internal_order_detail', pk=pk)
    order.indelivery_at=timezone.now()
    order.status = 'indelivery'
    order.save()
    messages.success(request, f'تم تحويل الطلبية رقم {order.order_number} إلى قيد التوصيل')
    return redirect('internal_order_list')

@login_required
def internal_order_receive(request, pk):
    order = get_object_or_404(InternalOrder, pk=pk)
    if order.status != 'indelivery':
        messages.error(request, 'لا يمكن تسليم طلبية غير قيد التوصيل')
        return redirect('internal_order_detail', pk=pk)
    
    with transaction.atomic():
        for item in order.items.all():
            inventory = Inventory.objects.filter(product=item.product).first()
            if inventory:
                if inventory.quantity < item.quantity:
                    messages.error(request, f'الكمية غير متوفرة للمنتج {item.product.name}')
                    return redirect('internal_order_detail', pk=pk)
        
        for item in order.items.all():
            inventory = Inventory.objects.filter(product=item.product).first()
            if inventory:
                inventory.quantity -= item.quantity
                inventory.save()
                
                InventoryMovement.objects.create(
                    product=item.product,
                    movement_type='sale',
                    quantity=-item.quantity,
                    notes=f'طلبية بيع {order.order_number}',
                    created_by=request.user
                )
        
        order.status = 'received'
        order.save()
        
        if order.customer:
            order.customer.debt_balance += order.debt_amount
            order.customer.save()
    
    messages.success(request, f'تم تسليم الطلبية رقم {order.order_number} بنجاح')
    return redirect('internal_order_list')

@login_required
def internal_order_cancel(request, pk):
    order = get_object_or_404(InternalOrder, pk=pk)
    if order.status in ['received', 'cancelled']:
        messages.error(request, 'لا يمكن إلغاء طلبية مكتملة أو ملغاة')
        return redirect('internal_order_detail', pk=pk)
    
    if order.status == 'confirmed':
        order.status = 'cancelled'
        order.debt_amount = 0
        order.save()
    elif order.status == 'indelivery':
        order.status = 'cancelled'
        order.debt_amount = 0
        order.save()
    else:
        order.status = 'cancelled'
        order.debt_amount = 0
        order.save()
    
    messages.success(request, f'تم إلغاء الطلبية رقم {order.order_number} بنجاح')
    return redirect('internal_order_list')

@login_required
def internal_order_delete(request, pk):
    order = get_object_or_404(InternalOrder, pk=pk)
    if order.status not in ['draft', 'cancelled']:
        messages.error(request, 'لا يمكن حذف طلبية غير مسودة أو ملغاة')
        return redirect('internal_order_detail', pk=pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'تم حذف الطلبية رقم {order_number} بنجاح')
        return redirect('internal_order_list')
    
    return render(request, 'orders/internal_order_confirm_delete.html', {'order': order})

def confirm_internal_order(order):
    with transaction.atomic():
        for item in order.items.all():
            inventory = Inventory.objects.filter(product=item.product).first()
            if not inventory or inventory.quantity < item.quantity:
                raise ValueError(f'الكمية غير متوفرة للمنتج {item.product.name}')

        order.status = 'confirmed'
        order.save()

@login_required
def get_product_inventory(request, product_id):
    inventory = Inventory.objects.filter(product_id=product_id).first()
    if inventory:
        data = {
            'quantity': inventory.quantity,
            'cost': inventory.lyd_total_cost,
            'sell_price': inventory.lyd_sell_price
        }
    else:
        data = {
            'quantity': 0,
            'cost': 0,
            'sell_price': 0
        }
    return JsonResponse(data)

@login_required
def external_commission_list(request):
    if not request.user.is_main_admin():
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
        return redirect('home')
    commissions = ExternalOrderCommission.objects.all()
    paginator = Paginator(commissions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'orders/external_commission_list.html', {'page_obj': page_obj})

@login_required
def external_commission_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        min_amount = request.POST.get('min_amount')
        max_amount = request.POST.get('max_amount')
        percentage = request.POST.get('percentage')
        fixed_amount_lyd  = request.POST.get('fixed_amount_lyd')
        if not name or not min_amount or not percentage:
            messages.error(request, 'جميع الحقول مطلوبة')
            return redirect('external_commission_add')
        
        ExternalOrderCommission.objects.create(
            name=name,
            min_amount=min_amount,
            max_amount=max_amount if max_amount else None,
            percentage=percentage,
            fixed_amount_lyd =fixed_amount_lyd 
        )
        messages.success(request, 'تم إضافة العمولة بنجاح')
        return redirect('external_commission_list')
    
    return render(request, 'orders/external_commission_form.html', {'title': 'إضافة عمولة'})

@login_required
def external_commission_edit(request, pk):
    commission = get_object_or_404(ExternalOrderCommission, pk=pk)
    if request.method == 'POST':
        commission.name = request.POST.get('name')
        commission.min_amount = request.POST.get('min_amount')
        commission.max_amount = request.POST.get('max_amount') if request.POST.get('max_amount') else None
        commission.percentage = request.POST.get('percentage')
        commission.fixed_amount_lyd = request.POST.get('fixed_amount_lyd')
        commission.save()
        messages.success(request, 'تم تحديث العمولة بنجاح')
        return redirect('external_commission_list')
    
    return render(request, 'orders/external_commission_form.html', {'commission': commission, 'title': 'تعديل عمولة'})

@login_required
def external_commission_delete(request, pk):
    commission = get_object_or_404(ExternalOrderCommission, pk=pk)
    if request.method == 'POST':
        commission.delete()
        messages.success(request, 'تم حذف العمولة بنجاح')
        return redirect('external_commission_list')
    return render(request, 'orders/external_commission_confirm_delete.html', {'commission': commission})

@login_required
def external_order_list(request):
    orders = ExternalOrder.objects.select_related('customer', 'commission_rule').all().order_by('-created_at')
    
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    supply_filter = request.GET.get('supply', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__full_name__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if supply_filter:
        orders = orders.filter(supply=supply_filter)
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    status_choices = ExternalOrder.STATUS_CHOICES
    supply_choices = ExternalOrder.SUPPLY
    
    return render(request, 'orders/external_order_list.html', {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'supply_choices': supply_choices,
        'search_query': search_query,
        'selected_status': status_filter,
        'selected_supply': supply_filter,
        'date_from': date_from,
        'date_to': date_to
    })

@login_required
def external_order_deliver(request, pk):
    order = get_object_or_404(ExternalOrder, pk=pk)
    if order.status != 'confirmed':
        messages.error(request, 'لا يمكن شحن طلبية غير مؤكدة')
        return redirect('external_order_list')
    
    order.status = 'indeliver'
    order.save()
    messages.success(request, f'تم تحويل الطلبية الخارجية رقم {order.order_number} إلى قيد التوصيل')
    return redirect('external_order_list')

@login_required
def external_order_receive(request, pk):
    order = get_object_or_404(ExternalOrder, pk=pk)
    if order.status != 'indeliver':
        messages.error(request, 'لا يمكن تسليم طلبية غير قيد التوصيل')
        return redirect('external_order_list')
    
    order.status = 'received'
    order.save()
    
    if order.customer:
        order.customer.debt_balance += order.lyd_debt_amount
        order.customer.save()
    
    messages.success(request, f'تم تسليم الطلبية الخارجية رقم {order.order_number} بنجاح')
    return redirect('external_order_list')

@login_required
def external_order_add(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        subtotal_usd = Decimal(request.POST.get('subtotal_usd', 0))
        discount_usd = Decimal(request.POST.get('discount_usd', 0))
        shipping_cost_usd = Decimal(request.POST.get('shipping_cost_usd', 0))
        exchange_rate = Decimal(request.POST.get('exchange_rate', 1))
        paid_amount_lyd = Decimal(request.POST.get('paid_amount_lyd', 0))
        delivery_address = request.POST.get('delivery_address', '')
        supply = request.POST.get('supply')
        status = request.POST.get('status', 'draft')
        
        product_names = request.POST.getlist('product_names[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices_usd = request.POST.getlist('unit_prices_usd[]')
        unit_discounts_usd = request.POST.getlist('unit_discounts_usd[]')
        product_links = request.POST.getlist('product_links[]')
        
        if not customer_id:
            messages.error(request, 'يرجى اختيار العميل')
            return redirect('external_order_add')
        
        if not product_names:
            messages.error(request, 'يرجى إضافة منتج واحد على الأقل')
            return redirect('external_order_add')
        
        shipping_cost_lyd = shipping_cost_usd * exchange_rate
        
        sales_total_usd = subtotal_usd - discount_usd + shipping_cost_usd
        sales_total_lyd = sales_total_usd * exchange_rate
        
        commission_rule = None
        commission_percentage = 0
        commission_amount_lyd = 0
        
        commission_rule = ExternalOrderCommission.objects.filter(
            min_amount__lte=sales_total_usd
        ).filter(
            Q(max_amount__isnull=True) | Q(max_amount__gte=sales_total_usd)
        ).first()
        
        if commission_rule:
            commission_percentage = commission_rule.percentage
            commission_data = commission_rule.calculate_commission(sales_total_usd, exchange_rate)
            commission_amount_lyd = commission_data['lyd']
        
        debt_amount_lyd = sales_total_lyd - paid_amount_lyd
        if debt_amount_lyd < 0:
            debt_amount_lyd = 0
        
        with transaction.atomic():
            order = ExternalOrder.objects.create(
                customer=Customer.objects.get(id=customer_id),
                subtotal=subtotal_usd,
                discount=discount_usd,
                usd_sales_total=sales_total_usd,
                lyd_sales_total=sales_total_lyd,
                lyd_paid_amount=paid_amount_lyd,
                lyd_debt_amount=debt_amount_lyd,
                delivery_address=delivery_address,
                supply=supply,
                status=status,
                exchange_rate=exchange_rate,
                commission_rule=commission_rule,
                commission_percentage=commission_percentage,
                lyd_commission_amount=commission_amount_lyd,
                usd_shipping_cost=shipping_cost_usd,
                lyd_shipping_cost=shipping_cost_lyd,
                total_profit=commission_amount_lyd
            )
            
            for i in range(len(product_names)):
                product_name = product_names[i]
                quantity = int(quantities[i])
                unit_price_usd = Decimal(unit_prices_usd[i]) if unit_prices_usd[i] else 0
                unit_discount_usd = Decimal(unit_discounts_usd[i]) if unit_discounts_usd[i] else 0
                product_link = product_links[i] if product_links[i] else ''
                
                unit_price_lyd = unit_price_usd * exchange_rate
                unit_discount_lyd = unit_discount_usd * exchange_rate
                total_usd = (unit_price_usd - unit_discount_usd) * quantity
                total_lyd = total_usd * exchange_rate
                
                ExternalOrderItem.objects.create(
                    order=order,
                    product_name=product_name,
                    product_link=product_link,
                    quantity=quantity,
                    usd_unit_discount=unit_discount_usd,
                    lyd_unit_price=unit_price_lyd,
                    lyd_total_price=total_lyd,
                    usd_unit_price=unit_price_usd,
                    usd_total_price=total_usd
                )
            
            messages.success(request, f'تم إنشاء الطلبية الخارجية رقم {order.order_number} بنجاح')
            return redirect('external_order_list')
    
    customers = Customer.objects.all().order_by('full_name')
    return render(request, 'orders/external_order_add.html', {
        'customers': customers
    })


@login_required
def external_order_edit(request, pk):
    order = get_object_or_404(ExternalOrder, pk=pk)
    if order.status not in ['draft', 'cancelled']:
        messages.error(request, 'لا يمكن تعديل طلبية غير مسودة أو ملغاة')
        return redirect('external_order_detail', pk=pk)
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        subtotal_usd = Decimal(request.POST.get('subtotal_usd', 0))
        discount_usd = Decimal(request.POST.get('discount_usd', 0))
        shipping_cost_usd = Decimal(request.POST.get('shipping_cost_usd', 0))
        exchange_rate = Decimal(request.POST.get('exchange_rate', 1))
        paid_amount_lyd = Decimal(request.POST.get('paid_amount_lyd', 0))
        delivery_address = request.POST.get('delivery_address', '')
        supply = request.POST.get('supply')
        status = request.POST.get('status', 'draft')
        
        product_names = request.POST.getlist('product_names[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices_usd = request.POST.getlist('unit_prices_usd[]')
        unit_discounts_usd = request.POST.getlist('unit_discounts_usd[]')
        product_links = request.POST.getlist('product_links[]')
        
        if not customer_id:
            messages.error(request, 'يرجى اختيار العميل')
            return redirect('external_order_edit', pk=pk)
        
        if not product_names:
            messages.error(request, 'يرجى إضافة منتج واحد على الأقل')
            return redirect('external_order_edit', pk=pk)
        
        shipping_cost_lyd = shipping_cost_usd * exchange_rate
        
        sales_total_usd = subtotal_usd - discount_usd + shipping_cost_usd
        sales_total_lyd = sales_total_usd * exchange_rate
        
        commission_rule = None
        commission_percentage = 0
        commission_amount_lyd = 0
        
        commission_rule = ExternalOrderCommission.objects.filter(
            min_amount__lte=sales_total_usd
        ).filter(
            Q(max_amount__isnull=True) | Q(max_amount__gte=sales_total_usd)
        ).first()
        
        if commission_rule:
            commission_percentage = commission_rule.percentage
            commission_data = commission_rule.calculate_commission(sales_total_usd, exchange_rate)
            commission_amount_lyd = commission_data['lyd']
        
        debt_amount_lyd = sales_total_lyd - paid_amount_lyd
        if debt_amount_lyd < 0:
            debt_amount_lyd = 0
        
        with transaction.atomic():
            order.customer = Customer.objects.get(id=customer_id)
            order.subtotal = subtotal_usd
            order.discount = discount_usd
            order.usd_sales_total = sales_total_usd
            order.lyd_sales_total = sales_total_lyd
            order.lyd_paid_amount = paid_amount_lyd
            order.lyd_debt_amount = debt_amount_lyd
            order.delivery_address = delivery_address
            order.supply = supply
            order.status = status
            order.exchange_rate = exchange_rate
            order.commission_rule = commission_rule
            order.commission_percentage = commission_percentage
            order.lyd_commission_amount = commission_amount_lyd
            order.usd_shipping_cost = shipping_cost_usd
            order.lyd_shipping_cost = shipping_cost_lyd
            order.total_profit = commission_amount_lyd
            order.save()
            
            order.items.all().delete()
            
            for i in range(len(product_names)):
                product_name = product_names[i]
                quantity = int(quantities[i])
                unit_price_usd = Decimal(unit_prices_usd[i]) if unit_prices_usd[i] else 0
                unit_discount_usd = Decimal(unit_discounts_usd[i]) if unit_discounts_usd[i] else 0
                product_link = product_links[i] if product_links[i] else ''
                
                unit_price_lyd = unit_price_usd * exchange_rate
                unit_discount_lyd = unit_discount_usd * exchange_rate
                total_usd = (unit_price_usd - unit_discount_usd) * quantity
                total_lyd = total_usd * exchange_rate
                
                ExternalOrderItem.objects.create(
                    order=order,
                    product_name=product_name,
                    product_link=product_link,
                    quantity=quantity,
                    usd_unit_discount=unit_discount_usd,
                    lyd_unit_price=unit_price_lyd,
                    lyd_total_price=total_lyd,
                    usd_unit_price=unit_price_usd,
                    usd_total_price=total_usd
                )
            
            messages.success(request, f'تم تحديث الطلبية الخارجية رقم {order.order_number} بنجاح')
            return redirect('external_order_list')
    
    customers = Customer.objects.all().order_by('full_name')
    return render(request, 'orders/external_order_edit.html', {
        'order': order,
        'customers': customers
    })



@login_required
def get_commission_rule(request):
    try:
        amount_usd = Decimal(str(request.GET.get('amount', 0)))
        exchange_rate = Decimal(str(request.GET.get('exchange_rate', 1)))
    except:
        return JsonResponse({
            'id': None,
            'name': 'خطأ في القيم',
            'percentage': 0,
            'fixed_amount_lyd': 0,
            'commission_usd': 0,
            'commission_lyd': 0,
            'percentage_amount_usd': 0,
            'percentage_amount_lyd': 0
        })
    
    commission = ExternalOrderCommission.objects.filter(
        min_amount__lte=amount_usd
    ).filter(
        Q(max_amount__isnull=True) | Q(max_amount__gte=amount_usd)
    ).first()
    
    if commission:
        commission_data = commission.calculate_commission(amount_usd, exchange_rate)
        return JsonResponse({
            'id': commission.id,
            'name': commission.name,
            'percentage': float(commission.percentage),
            'fixed_amount_lyd': float(commission.fixed_amount_lyd),
            'commission_usd': float(commission_data['usd']),
            'commission_lyd': float(commission_data['lyd']),
            'percentage_amount_usd': float(commission_data['percentage_amount_usd']),
            'percentage_amount_lyd': float(commission_data['percentage_amount_lyd'])
        })
    else:
        return JsonResponse({
            'id': None,
            'name': 'لا توجد عمولة',
            'percentage': 0,
            'fixed_amount_lyd': 0,
            'commission_usd': 0,
            'commission_lyd': 0,
            'percentage_amount_usd': 0,
            'percentage_amount_lyd': 0
        })

@login_required
def external_order_detail(request, pk):
    order = get_object_or_404(ExternalOrder, pk=pk)
    return render(request, 'orders/external_order_detail.html', {'order': order})

@login_required
def external_order_confirm(request, pk):
    order = get_object_or_404(ExternalOrder, pk=pk)

    order.status = 'confirmed'
    order.save()
    if order.customer:
        customer=order.customer
        customer.debt_balance += order.lyd_debt_amount
        customer.save()
    messages.success(request, f'تم تأكيد الطلبية الخارجية رقم {order.order_number} بنجاح')
    return redirect('external_order_list')

@login_required
def external_order_cancel(request, pk):
    order = get_object_or_404(ExternalOrder, pk=pk)
    if order.status == 'cancelled':
        messages.error(request, 'الطلبية ملغاة بالفعل')
        return redirect('external_order_detail', pk=pk)
    
    order.status = 'cancelled'
    order.lyd_debt_amount = 0
    order.save()
    messages.success(request, f'تم إلغاء الطلبية الخارجية رقم {order.order_number} بنجاح')
    return redirect('external_order_list')

@login_required
def external_order_delete(request, pk):
    order = get_object_or_404(ExternalOrder, pk=pk)
    if order.status not in ['draft', 'cancelled']:
        messages.error(request, 'لا يمكن حذف طلبية غير مسودة أو ملغاة')
        return redirect('external_order_detail', pk=pk)
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'تم حذف الطلبية الخارجية رقم {order_number} بنجاح')
        return redirect('external_order_list')
    
    return render(request, 'orders/external_order_confirm_delete.html', {'order': order})


@login_required
def reports_dashboard(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            date_from = timezone.now().date() - timedelta(days=30)
    else:
        date_from = timezone.now().date() - timedelta(days=30)
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            date_to = timezone.now().date()
    else:
        date_to = timezone.now().date()
    
    internal_orders = InternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    external_orders = ExternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    expenses = Expense.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    total_internal_orders = internal_orders.count()
    total_external_orders = external_orders.count()
    total_orders = total_internal_orders + total_external_orders
    
    total_sales_internal = internal_orders.filter(
        status__in=['confirmed', 'indelivery', 'received']
    ).aggregate(total=Sum('sales_total'))['total'] or Decimal('0')
    
    total_sales_external = external_orders.filter(
        status__in=['confirmed', 'indeliver', 'received']
    ).aggregate(total=Sum('lyd_sales_total'))['total'] or Decimal('0')
    
    total_sales = total_sales_internal + total_sales_external
    
    total_profit_internal = internal_orders.filter(
        status__in=['confirmed', 'indelivery', 'received']
    ).aggregate(total=Sum('total_profit'))['total'] or Decimal('0')
    
    total_profit_external = external_orders.filter(
        status__in=['confirmed', 'indeliver', 'received']
    ).aggregate(total=Sum('lyd_commission_amount'))['total'] or Decimal('0')
    
    total_profit = total_profit_internal + total_profit_external
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    net_profit = total_profit - total_expenses
    
    total_internal_received = internal_orders.filter(status='received').count()
    total_external_received = external_orders.filter(status='received').count()
    total_received = total_internal_received + total_external_received
    
    total_confirmed_orders = internal_orders.filter(
        status__in=['confirmed', 'indelivery']
    ).count() + external_orders.filter(
        status__in=['confirmed', 'indeliver']
    ).count()
    
    delivery_rate = 0
    if total_orders > 0:
        delivery_rate = round((total_received / total_orders) * 100, 2)
    
    top_products = get_top_products(date_from, date_to)
    top_customers = get_top_customers(date_from, date_to)
    top_expense_categories = get_top_expense_categories(date_from, date_to)
    order_status_counts = get_order_status_counts(date_from, date_to)
    daily_sales = get_daily_sales(date_from, date_to)
    
    # بيانات الرسوم البيانية - المبيعات اليومية
    chart_labels = []
    chart_internal_sales = []
    chart_external_sales = []
    chart_total_sales = []
    
    for day in daily_sales:
        chart_labels.append(day['date'])
        chart_internal_sales.append(float(day['internal']))
        chart_external_sales.append(float(day['external']))
        chart_total_sales.append(float(day['total']))
    
    # بيانات حالة الطلبات للرسم الدائري
    pie_labels = []
    pie_data = []
    pie_colors = []
    
    status_colors = {
        'مستلمة': '#16a34a',
        'مؤكدة': '#af006b',
        'قيد التوصيل': '#f59e0b',
        'في التوصيل': '#f59e0b',
        'مسودة': '#6b7280',
        'ملغاة': '#dc2626'
    }
    
    for item in order_status_counts:
        pie_labels.append(item['status'])
        pie_data.append(item['count'])
        pie_colors.append(status_colors.get(item['status'], '#6b7280'))
    
    # بيانات المنتجات الأكثر مبيعاً
    product_names = []
    product_quantities = []
    
    for product in top_products[:10]:
        product_names.append(product['name'])
        product_quantities.append(product['quantity'])
    
    # بيانات العملاء الأكثر طلباً
    customer_names = []
    customer_spent = []
    
    for customer in top_customers[:10]:
        customer_names.append(customer['name'])
        customer_spent.append(float(customer['spent']))
    
    # بيانات المصروفات
    expense_names = []
    expense_amounts = []
    
    for category in top_expense_categories[:10]:
        expense_names.append(category['name'])
        expense_amounts.append(float(category['amount']))
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_orders': total_orders,
        'total_internal_orders': total_internal_orders,
        'total_external_orders': total_external_orders,
        'total_sales': total_sales,
        'total_sales_internal': total_sales_internal,
        'total_sales_external': total_sales_external,
        'total_profit': total_profit,
        'total_profit_internal': total_profit_internal,
        'total_profit_external': total_profit_external,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_received': total_received,
        'total_confirmed_orders': total_confirmed_orders,
        'delivery_rate': delivery_rate,
        'top_products': top_products,
        'top_customers': top_customers,
        'top_expense_categories': top_expense_categories,
        'order_status_counts': order_status_counts,
        'daily_sales': daily_sales,
        'chart_labels': chart_labels,
        'chart_internal_sales': chart_internal_sales,
        'chart_external_sales': chart_external_sales,
        'chart_total_sales': chart_total_sales,
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'pie_colors': pie_colors,
        'product_names': product_names,
        'product_quantities': product_quantities,
        'customer_names': customer_names,
        'customer_spent': customer_spent,
        'expense_names': expense_names,
        'expense_amounts': expense_amounts,
    }
    
    return render(request, 'dashboard/reports.html', context)


def get_top_products(date_from, date_to):
    from collections import defaultdict
    
    product_data = defaultdict(lambda: {'quantity': 0, 'revenue': 0})
    
    internal_items = InternalOrderItem.objects.filter(
        order__created_at__date__gte=date_from,
        order__created_at__date__lte=date_to,
        order__status__in=['confirmed', 'indelivery', 'received']
    ).select_related('product')
    
    for item in internal_items:
        product_data[item.product.name]['quantity'] += item.quantity
        product_data[item.product.name]['revenue'] += item.total_price
    
    external_items = ExternalOrderItem.objects.filter(
        order__created_at__date__gte=date_from,
        order__created_at__date__lte=date_to,
        order__status__in=['confirmed', 'indeliver', 'received']
    )
    
    for item in external_items:
        product_data[item.product_name]['quantity'] += item.quantity
        product_data[item.product_name]['revenue'] += item.lyd_total_price
    
    sorted_products = sorted(
        product_data.items(), 
        key=lambda x: x[1]['quantity'], 
        reverse=True
    )[:10]
    
    return [
        {
            'name': name,
            'quantity': data['quantity'],
            'revenue': data['revenue']
        }
        for name, data in sorted_products
    ]


def get_top_customers(date_from, date_to):
    from collections import defaultdict
    
    customer_data = defaultdict(lambda: {'orders': 0, 'spent': 0})
    
    internal_orders = InternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['confirmed', 'indelivery', 'received'],
        customer__isnull=False
    ).select_related('customer')
    
    for order in internal_orders:
        if order.customer:
            customer_data[order.customer.full_name]['orders'] += 1
            customer_data[order.customer.full_name]['spent'] += order.sales_total
    
    external_orders = ExternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['confirmed', 'indeliver', 'received'],
        customer__isnull=False
    ).select_related('customer')
    
    for order in external_orders:
        if order.customer:
            customer_data[order.customer.full_name]['orders'] += 1
            customer_data[order.customer.full_name]['spent'] += order.lyd_sales_total
    
    sorted_customers = sorted(
        customer_data.items(),
        key=lambda x: x[1]['spent'],
        reverse=True
    )[:10]
    
    return [
        {
            'name': name,
            'orders': data['orders'],
            'spent': data['spent']
        }
        for name, data in sorted_customers
    ]


def get_top_expense_categories(date_from, date_to):
    from collections import defaultdict
    
    expense_data = defaultdict(lambda: 0)
    
    expenses = Expense.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        category__isnull=False
    ).select_related('category')
    
    for expense in expenses:
        expense_data[expense.category.name] += expense.amount
    
    sorted_expenses = sorted(
        expense_data.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return [
        {
            'name': name,
            'amount': amount
        }
        for name, amount in sorted_expenses
    ]


def get_order_status_counts(date_from, date_to):
    internal_counts = InternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('status').annotate(count=Count('id'))
    
    external_counts = ExternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('status').annotate(count=Count('id'))
    
    status_map = {}
    
    for item in internal_counts:
        status_map[item['status']] = status_map.get(item['status'], 0) + item['count']
    
    for item in external_counts:
        status_map[item['status']] = status_map.get(item['status'], 0) + item['count']
    
    status_labels = {
        'draft': 'مسودة',
        'confirmed': 'مؤكدة',
        'indelivery': 'قيد التوصيل',
        'indeliver': 'في التوصيل',
        'received': 'مستلمة',
        'cancelled': 'ملغاة'
    }
    
    return [
        {
            'status': status_labels.get(key, key),
            'count': value
        }
        for key, value in status_map.items()
    ]


def get_daily_sales(date_from, date_to):
    from collections import defaultdict
    
    daily_data = defaultdict(lambda: {'internal': 0, 'external': 0})
    
    internal_orders = InternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['confirmed', 'indelivery', 'received']
    ).values('created_at__date').annotate(total=Sum('sales_total'))
    
    for item in internal_orders:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        daily_data[date_str]['internal'] += item['total'] or 0
    
    external_orders = ExternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['confirmed', 'indeliver', 'received']
    ).values('created_at__date').annotate(total=Sum('lyd_sales_total'))
    
    for item in external_orders:
        date_str = item['created_at__date'].strftime('%Y-%m-%d')
        daily_data[date_str]['external'] += item['total'] or 0
    
    sorted_dates = sorted(daily_data.keys())
    
    return [
        {
            'date': date,
            'internal': daily_data[date]['internal'],
            'external': daily_data[date]['external'],
            'total': daily_data[date]['internal'] + daily_data[date]['external']
        }
        for date in sorted_dates
    ]


@login_required
def marketing_dashboard(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            date_from = timezone.now().date() - timedelta(days=90)
    else:
        date_from = timezone.now().date() - timedelta(days=90)
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            date_to = timezone.now().date()
    else:
        date_to = timezone.now().date()
    
    total_customers = Customer.objects.count()
    new_customers = Customer.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).count()
    
    source_data = Customer.objects.values('known_us_from').annotate(
        count=Count('id')
    ).order_by('-count')
    
    source_labels = []
    source_counts = []
    source_colors = []
    
    source_colors_map = {
        'facebook': '#1877f2',
        'instagram': '#e4405f',
        'tiktok': '#000000',
        'snapchat': '#fffc00',
        'friend': '#16a34a',
        'advertisement': '#f59e0b',
        'other': '#6b7280'
    }
    
    source_names = {
        'facebook': 'فيسبوك',
        'instagram': 'إنستغرام',
        'tiktok': 'تيكتوك',
        'snapchat': 'سناب شات',
        'friend': 'صديق',
        'advertisement': 'إعلان',
        'other': 'أخرى'
    }
    
    for item in source_data:
        if item['known_us_from']:
            source_labels.append(source_names.get(item['known_us_from'], item['known_us_from']))
            source_counts.append(item['count'])
            source_colors.append(source_colors_map.get(item['known_us_from'], '#6b7280'))
    
    top_customers = get_marketing_top_customers(date_from, date_to)
    
    new_customers_by_source = Customer.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('known_us_from').annotate(
        count=Count('id')
    ).order_by('-count')
    
    new_source_labels = []
    new_source_counts = []
    
    for item in new_customers_by_source:
        if item['known_us_from']:
            new_source_labels.append(source_names.get(item['known_us_from'], item['known_us_from']))
            new_source_counts.append(item['count'])
    
    from django.db.models import Count
    
    repeat_customers = Customer.objects.annotate(
        order_count=Count('internalorder') + Count('externalorder')
    ).filter(order_count__gt=1).count()
    
    repeat_rate = 0
    if total_customers > 0:
        repeat_rate = round((repeat_customers / total_customers) * 100, 2)
    
    total_orders = InternalOrder.objects.count() + ExternalOrder.objects.count()
    avg_orders_per_customer = 0
    if total_customers > 0:
        avg_orders_per_customer = round(total_orders / total_customers, 2)
    
    monthly_new_customers = get_monthly_new_customers(date_from, date_to)
    
    monthly_labels = []
    monthly_counts = []
    
    for item in monthly_new_customers:
        monthly_labels.append(item['month'])
        monthly_counts.append(item['count'])
    customer_names = []
    customer_spent = []
    
    for customer in top_customers[:10]:
        customer_names.append(customer['name'])
        customer_spent.append(float(customer['spent']))
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'repeat_customers': repeat_customers,
        'repeat_rate': repeat_rate,
        'avg_orders_per_customer': avg_orders_per_customer,
        'source_labels': source_labels,
        'source_counts': source_counts,
        'source_colors': source_colors,
        'new_source_labels': new_source_labels,
        'new_source_counts': new_source_counts,
        'top_customers': top_customers,
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts,
        'customer_names': customer_names,
        'customer_spent': customer_spent,
    }
    
    return render(request, 'dashboard/marketing.html', context)


def get_marketing_top_customers(date_from, date_to):
    from collections import defaultdict
    
    customer_data = defaultdict(lambda: {'orders': 0, 'spent': 0, 'last_order': None})
    
    internal_orders = InternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['confirmed', 'indelivery', 'received'],
        customer__isnull=False
    ).select_related('customer').order_by('-created_at')
    
    for order in internal_orders:
        if order.customer:
            customer_data[order.customer.full_name]['orders'] += 1
            customer_data[order.customer.full_name]['spent'] += order.sales_total
            if not customer_data[order.customer.full_name]['last_order'] or order.created_at > customer_data[order.customer.full_name]['last_order']:
                customer_data[order.customer.full_name]['last_order'] = order.created_at
    
    external_orders = ExternalOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['confirmed', 'indeliver', 'received'],
        customer__isnull=False
    ).select_related('customer').order_by('-created_at')
    
    for order in external_orders:
        if order.customer:
            customer_data[order.customer.full_name]['orders'] += 1
            customer_data[order.customer.full_name]['spent'] += order.lyd_sales_total
            if not customer_data[order.customer.full_name]['last_order'] or order.created_at > customer_data[order.customer.full_name]['last_order']:
                customer_data[order.customer.full_name]['last_order'] = order.created_at
    
    sorted_customers = sorted(
        customer_data.items(),
        key=lambda x: x[1]['spent'],
        reverse=True
    )[:10]
    
    return [
        {
            'name': name,
            'orders': data['orders'],
            'spent': data['spent'],
            'last_order': data['last_order']
        }
        for name, data in sorted_customers
    ]


def get_monthly_new_customers(date_from, date_to):
    from collections import defaultdict
    
    monthly_data = defaultdict(int)
    
    customers = Customer.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    for customer in customers:
        month_key = customer.created_at.strftime('%Y-%m')
        monthly_data[month_key] += 1
    
    sorted_months = sorted(monthly_data.keys())
    
    return [
        {
            'month': month,
            'count': monthly_data[month]
        }
        for month in sorted_months
    ]