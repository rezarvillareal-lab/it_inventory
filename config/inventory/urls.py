from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [

    path("", views.dashboard, name="dashboard"),

    path("inventory/", views.inventory_list, name="inventory_list"),

    path("add/", views.inventory_create, name="inventory_add"),

    path("<int:pk>/", views.inventory_detail, name="inventory_detail"),

    path("<int:pk>/edit/", views.inventory_update, name="inventory_edit"),

    path("<int:pk>/delete/", views.inventory_delete, name="inventory_delete"),

    path("reports/", views.reports, name="reports"),

    path('reports/export/csv/', views.export_inventory_csv, name='export_csv'),

    path('reports/export/excel/', views.export_inventory_excel, name='export_excel'),
    
]