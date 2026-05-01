from django.shortcuts import render, redirect, get_object_or_404
from .forms import expenseform
from .models import Expenses
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Sum
import calendar
import matplotlib
matplotlib.use('Agg')  # ✅ Avoid GUI error for matplotlib
import matplotlib.pyplot as plt
import io
import base64

# ✅ Add Expense
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = expenseform(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('add_expense')
    else:
        form = expenseform()
    return render(request, 'add_expense.html', {'form': form})

# ✅ List Expenses
@login_required
def expense_list(request):
    expenses = Expenses.objects.filter(user=request.user).order_by('-date')

    category = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if category:
        expenses = expenses.filter(category=category)
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    categories = Expenses.CATEGORY_CHOICES

    context = {
        'expenses': expenses,
        'categories': categories,
        'selected_category': category,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'expense_list.html', context)

# ✅ Update Expense
@login_required
def update_expense(request, pk):
    expense = get_object_or_404(Expenses, pk=pk, user=request.user)

    if request.method == 'POST':
        form = expenseform(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = expenseform(instance=expense)

    return render(request, 'update_expense.html', {'form': form})

# ✅ Generate Pie Chart

def get_pie_chart(by_category):
    labels = [item['category'] for item in by_category]
    sizes = [item['total'] for item in by_category]
    colors = plt.cm.Pastel1.colors

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax.axis('equal')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_png = buf.read()
    buf.close()

    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

# ✅ Generate Bar Chart for Daily Expenses

def get_bar_chart(daily_data):
    fig, ax = plt.subplots()
    ax.bar(range(1, len(daily_data)+1), daily_data, color='#4f85ba')
    ax.set_title('Daily Expenses')
    ax.set_xlabel('Day of Month')
    ax.set_ylabel('Amount (₹)')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_png = buf.read()
    buf.close()

    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

# ✅ Generate Line Chart for Category Spending Pattern

def get_line_chart(by_category):
    labels = [item['category'] for item in by_category]
    values = [item['total'] for item in by_category]

    fig, ax = plt.subplots()
    ax.plot(labels, values, marker='o', linestyle='-', color='#e67e22')
    ax.set_title('Spending Distribution')
    ax.set_ylabel('Amount (₹)')
    ax.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_png = buf.read()
    buf.close()

    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

# ✅ Dashboard View with Month-Year Filter
@login_required
def dashboard_view(request):
    user = request.user

    selected_date = request.GET.get('month_year')
    if selected_date:
        selected_year, selected_month = map(int, selected_date.split('-'))
    else:
        today = datetime.today()
        selected_month = today.month
        selected_year = today.year

    expenses = Expenses.objects.filter(
        user=user,
        date__month=selected_month,
        date__year=selected_year
    )

    if not expenses.exists():
        return render(request, 'dashboard.html', {
            'no_data': True,
            'selected_date': datetime(selected_year, selected_month, 1)
        })

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0
    by_category = list(expenses.values('category').annotate(total=Sum('amount')))

    days = calendar.monthrange(selected_year, selected_month)[1]
    daily_data = [0] * days
    for e in expenses:
        daily_data[e.date.day - 1] += e.amount

    # 🏷️ Most Expensive Category
    most_expensive = max(by_category, key=lambda x: x['total'])['category'] if by_category else None

    # 📅 Date of Highest Spending
    highest_spending_day = max(range(len(daily_data)), key=lambda i: daily_data[i]) + 1 if daily_data else None

    pie_chart = get_pie_chart(by_category)
    bar_chart = get_bar_chart(daily_data)
    line_chart = get_line_chart(by_category)
    month_name = datetime(1900, selected_month, 1).strftime('%B')

    return render(request, 'dashboard.html', {
        'no_data': False,
        'total': total,
        'by_category': by_category,
        'daily_data': daily_data,
        'month_name': month_name,
        'year': selected_year,
        'pie_chart': pie_chart,
        'bar_chart': bar_chart,
        'line_chart': line_chart,
        'selected_date': datetime(selected_year, selected_month, 1),
        'most_expensive': most_expensive,
        'highest_spending_day': highest_spending_day,
    })
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import GroupExpenseSplitForm
from .models import Expenses
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP
from .forms import GroupExpenseSplitForm
from .models import Expenses
from django.contrib.auth.models import User


@login_required
@login_required
def split_group_expense(request):
    split_data = []
    invalid_emails = []

    if request.method == 'POST':
        form = GroupExpenseSplitForm(request.POST)
        if form.is_valid():
            expense_name = form.cleaned_data['expense_name']
            amount = form.cleaned_data['amount']
            category = form.cleaned_data['category']
            date = form.cleaned_data['date']
            emails_raw = form.cleaned_data['emails']

            email_list = [email.strip() for email in emails_raw.split(',') if email.strip()]
            email_list = list(set(email_list))  # remove duplicates

            users = User.objects.filter(email__in=email_list)
            valid_user_count = users.count() + 1  # including self

            if valid_user_count < 2:
                messages.error(request, "❌ Please enter at least one valid email of a registered user.")
                return redirect('split_group_expense')

            # Amount per person
            share = (amount / valid_user_count).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # 1. Add for current user
            Expenses.objects.create(
                user=request.user,
                expense_name=f"[Split] {expense_name}",
                amount=share,
                category=category,
                date=date
            )
            split_data.append({
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'amount': share
            })

            # 2. Add for each valid user
            for user in users.exclude(id=request.user.id):
                Expenses.objects.create(
                    user=user,
                    expense_name=f"[Shared] {expense_name} (split by {request.user.username})",
                    amount=share,
                    category=category,
                    date=date
                )
                split_data.append({
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'amount': share
                })

            # 3. Capture invalid emails
            registered_emails = set(users.values_list('email', flat=True))
            invalid_emails = list(set(email_list) - registered_emails)

            return render(request, 'split_group_expense.html', {
                'form': form,
                'split_data': split_data,
                'invalid_emails': invalid_emails
            })

    else:
        form = GroupExpenseSplitForm()

    return render(request, 'split_group_expense.html', {'form': form})
