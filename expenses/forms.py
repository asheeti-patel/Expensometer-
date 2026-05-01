from django import forms
from .models import Expenses
from django.contrib.auth.models import User

class expenseform(forms.ModelForm):
    class Meta:
        model=Expenses
        fields = ['expense_name', 'amount', 'category', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }
class GroupExpenseSplitForm(forms.Form):
    expense_name = forms.CharField(max_length=100)
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    category = forms.ChoiceField(choices=[
        ('Food', 'Food'),
        ('Shopping', 'Shopping'),
        ('Gifts', 'Gifts'),
        ('Transport', 'Transport'),
    ])
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    emails = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Enter emails separated by commas"}),
        help_text="Enter emails of people to split with, separated by commas."
    )