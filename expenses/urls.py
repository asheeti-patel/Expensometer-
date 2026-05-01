from django.urls import path
from . import views

urlpatterns=[
    path('add/',views.add_expense, name='add_expense'),
    path('', views.expense_list, name='expense_list'),
    path('expenses/update/<int:pk>/',views.update_expense,name='update_expense'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('split-group-expense/', views.split_group_expense, name='split_group_expense'),

    
]
