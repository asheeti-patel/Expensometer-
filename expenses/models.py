from django.db import models
from django.contrib.auth.models import User

# ✅ Group Model for Shared Expenses
class ExpenseGroup(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='expense_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# ✅ Expense Model
class Expenses(models.Model):
    CATEGORY_CHOICES = [
        ('Gifts', 'Gifts'),
        ('Food', 'Food'),
        ('Shopping', 'Shopping'),
        ('Transport', 'Transport'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expense_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    date = models.DateField()

    # ✅ New fields for group & split
    group = models.ForeignKey(ExpenseGroup, on_delete=models.SET_NULL, null=True, blank=True)
    is_split = models.BooleanField(default=False)  # To mark auto-created splits

    def __str__(self):
        return f"{self.expense_name} - {self.category} - ₹{self.amount}"

    def save(self, *args, **kwargs):
        new_expense = self.pk is None
        super().save(*args, **kwargs)

        # ✅ If new group expense & not already split, divide among members
        if new_expense and self.group and not self.is_split:
            members = self.group.members.exclude(id=self.user.id)
            if members.exists():
                split_amount = round(self.amount / (members.count() + 1), 2)

                for member in members:
                    Expenses.objects.create(
                        user=member,
                        expense_name=f"Shared: {self.expense_name}",
                        amount=split_amount,
                        category=self.category,
                        date=self.date,
                        group=self.group,
                        is_split=True
                    )
