from django.urls import path
from . import views
from django.contrib import admin

app_name = "inventory"

urlpatterns = [

    path("", views.home_redirect, name="home"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("inventory/", views.inventory_list, name="inventory_list"),

    path("inventory/export/csv/", views.export_inventory_search_csv, name="inventory_export_csv"),

    path("inventory/export/excel/", views.export_inventory_search_excel, name="inventory_export_excel"),

    path("add/", views.inventory_create, name="inventory_add"),

    path("<int:pk>/print/", views.inventory_print, name="inventory_print"),

    path("<int:pk>/", views.inventory_detail, name="inventory_detail"),

    path("<int:pk>/edit/", views.inventory_update, name="inventory_edit"),

    path("<int:pk>/delete/", views.inventory_delete, name="inventory_delete"),

    path("reports/", views.reports, name="reports"),

    path('reports/export/csv/', views.export_inventory_csv, name='export_csv'),

    path('reports/export/excel/', views.export_inventory_excel, name='export_excel'),

    path('admin/', admin.site.urls),

       
]

handler403 = 'inventory.views.custom_403_view'