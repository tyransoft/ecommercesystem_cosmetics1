from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.utils import timezone
from django.forms import inlineformset_factory


WIDGET_ATTRS = {
    'class': 'form-control',
    'placeholder': 'أدخل النص هنا'
}

SELECT_ATTRS = {
    'class': 'form-select'
}

DATE_ATTRS = {
    'class': 'form-control',
    'type': 'date'
      
}



class LoginForm(forms.Form):
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم المستخدم', 'autofocus': True})
    )
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'أدخل كلمة المرور'})
    )


class UserCreateForm(UserCreationForm):
    role = forms.ChoiceField(label='الدور', choices=Role.choices, widget=forms.Select(attrs={'class': 'form-select'}))


    class Meta:
        model = CustomUser
        fields = ['username', 'role',  'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].label = 'كلمة المرور'
        self.fields['password2'].label = 'تأكيد كلمة المرور'


class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [ 'role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'role': 'الدور',
            'is_active': 'نشط',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)




class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
        }


class ProductForm(forms.ModelForm):
    brand_choices = forms.CharField(widget=forms.HiddenInput(), required=False)
    class Meta:
        model = Product
        fields = ['name', 'category', 'brand', 'made_in', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'اسم المنتج'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'الماركة',
                'autocomplete': 'off',
                'id': 'id_brand'
            }),
            'made_in': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'صنع في'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'
            }),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'color', 'size', 'edition', 'barcode',
                  'usd_sell_price', 'lyd_sell_price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'variant-field w-full px-3 py-2 rounded-lg border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'اسم النسخة'
            }),
            'color': forms.TextInput(attrs={
                'class': 'variant-field w-full px-3 py-2 rounded-lg border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'اللون/الدرجة'
            }),
            'size': forms.TextInput(attrs={
                'class': 'variant-field w-full px-3 py-2 rounded-lg border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'الحجم'
            }),
            'edition': forms.TextInput(attrs={
                'class': 'variant-field w-full px-3 py-2 rounded-lg border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'الإصدار'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'variant-field w-full px-3 py-2 rounded-lg border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'الباركود'
            }),
            'usd_sell_price': forms.NumberInput(attrs={
                'class': 'variant-field w-full px-3 py-2 rounded-lg border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'lyd_sell_price': forms.NumberInput(attrs={
                'class': 'variant-field w-full px-3 py-2 rounded-lg border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 accent-primary'
            }),
        }


ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'phone',  'city', 'known_us_from']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'known_us_from': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
        }
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('رقم الهاتف مطلوب')
        qs = Customer.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('رقم الهاتف مسجل من قبل')
        return phone
class CustomerPaymentForm(forms.ModelForm):
    class Meta:
        model = CustomerPayment
        fields = ['amount', 'payment_date', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'step': '0.01'}),
            'payment_date': forms.DateTimeInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'rows': 3}),
        }        



class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name','supplier_cuntry','supplier_carrency','supplier_kind','phone','website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'supplier_cuntry': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'supplier_carrency': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'supplier_kind': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'website': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),

        }

class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ['amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'reference_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'rows': 3}),
        }        


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'rows': 3}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'payment_method', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'payment_method': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'rows': 3}),
        }        