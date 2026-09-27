from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.utils import timezone

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
    BRAND_CHOICES = [
        'Anastasia Beverly Hills', 'Beauty of Joseon', 'Benefit Cosmetics',
        'Biodance', 'BYOMA', 'Caudalie', 'Chanel', 'Charlotte Tilbury',
        'Clinique', 'Color Wow', 'Danessa Myricks Beauty', 'Dior',
        'Dolce & Gabbana', 'e.l.f. Cosmetics', 'Estée Lauder',
        'Fable & Mane', 'Fenty Beauty', 'Gisou', 'Givenchy',
        'Glow Recipe', 'Grande Cosmetics', 'Gucci', 'Haus Labs',
        'Hourglass Cosmetics', 'Huda Beauty', 'ICONIC London',
        'ILIA Beauty', 'IT Cosmetics', 'K18 Hair', 'Kérastase',
        'Kiehl’s', 'Kosas', 'Lancôme', 'LANEIGE', 'Laura Geller Beauty',
        'Laura Mercier', 'L’Occitane en Provence', 'L’Oréal Paris',
        'LYS Beauty', 'MAC Cosmetics', 'MAKE UP FOR EVER',
        'Makeup by Mario', 'MERIT Beauty', 'Milk Makeup', 'NARS Cosmetics',
        'Natasha Denona', 'OLAPLEX', 'ONE/SIZE by Patrick Starrr',
        'Patrick Ta Beauty', 'Paula’s Choice', 'Prada Beauty',
        'Rare Beauty', 'REFY', 'Rhode', 'Saie', 'SEPHORA COLLECTION',
        'Sol de Janeiro', 'Supergoop!', 'Tarte Cosmetics',
        'The INKEY List', 'The Ordinary', 'Too Faced', 'Tower 28 Beauty',
        'Urban Decay', 'YSL Beauty',
    ]

    class Meta:
        model = Product
        fields = ['name', 'barcode', 'category', 'image', 'brand', 'color',
                  'made_in', 'usd_sell_price', 'lyd_sell_price']
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200',
                'placeholder': 'اختر أو اكتب اسم البراند',
                'autocomplete': 'off',
            }),
             'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'barcode': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'color': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'made_in': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200'}),
            'usd_sell_price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'step': '0.1'}),

            'lyd_sell_price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-secondary-container focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200', 'step': '0.1'}),


        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand_choices = self.BRAND_CHOICES

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