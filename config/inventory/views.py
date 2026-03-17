import csv

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Q
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl import Workbook

from .forms import InventoryForm
from .models import EquipmentComponent, Inventory


def _inventory_search_queryset(request):
    query = (request.GET.get("q") or "").strip()

    inventories = Inventory.objects.all().order_by("-created_at")

    if query:
        inventories = inventories.filter(
            Q(control_number__icontains=query)
            | Q(user_name__icontains=query)
            | Q(computer_name__icontains=query)
            | Q(assigned_ip__icontains=query)
            | Q(office_or_hospital__icontains=query)
        )

    return inventories, query


def inventory_list(request):
    inventories, query = _inventory_search_queryset(request)

    return render(
        request,
        "inventory/inventory_list.html",
        {"inventories": inventories, "query": query},
    )


def reports(request):

    office_report = (
        Inventory.objects
        .values("office_or_hospital")
        .annotate(total=Count("id"))
        .order_by("office_or_hospital")
    )

    status_report = (
        Inventory.objects
        .values("status")
        .annotate(total=Count("id"))
    )

    context = {
        "office_report": office_report,
        "status_report": status_report
    }

    return render(request, "inventory/reports.html", context)

def export_inventory_csv(request):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'

    writer = csv.writer(response)

    writer.writerow([
        'Control Number',
        'User Name',
        'Computer Name',
        'Assigned IP',
        'Office',
        'Status'
    ])

    inventories = Inventory.objects.all()

    for item in inventories:
        writer.writerow([
            item.control_number,
            item.user_name,
            item.computer_name,
            item.assigned_ip,
            item.office_or_hospital,
            item.status
        ])

    return response


def export_inventory_excel(request):

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inventory Report"

    sheet.append([
        "Control Number",
        "User Name",
        "Computer Name",
        "Assigned IP",
        "Office",
        "Status"
    ])

    inventories = Inventory.objects.all()

    for item in inventories:
        sheet.append([
            item.control_number,
            item.user_name,
            item.computer_name,
            item.assigned_ip,
            item.office_or_hospital,
            item.status
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = 'attachment; filename=inventory_report.xlsx'

    workbook.save(response)

    return response


# STATIC EQUIPMENT FORM (no dropdown)
class EquipmentStaticForm(forms.Form):
    equipment_name = forms.CharField(
    widget=forms.TextInput(attrs={'readonly': 'readonly'})
)
    original_model = forms.CharField(required=False)
    original_serial = forms.CharField(required=False)
    replacement_model = forms.CharField(required=False)
    replacement_serial = forms.CharField(required=False)
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1}))


def dashboard(request):

    total_computers = Inventory.objects.count()

    active_count = Inventory.objects.filter(status="Active").count()
    maintenance_count = Inventory.objects.filter(status="Maintenance").count()
    condemned_count = Inventory.objects.filter(status="Condemned").count()

    offices = (
        Inventory.objects
        .values("office_or_hospital")
        .annotate(total=Count("id"))
    )

    office_labels = [o["office_or_hospital"] for o in offices]
    office_counts = [o["total"] for o in offices]

    statuses = (
        Inventory.objects
        .values("status")
        .annotate(total=Count("id"))
    )

    status_labels = [s["status"] for s in statuses]
    status_counts = [s["total"] for s in statuses]

    recent_inventory = Inventory.objects.all().order_by("-created_at")[:5]

    context = {
        "total_computers": total_computers,
        "active_count": active_count,
        "maintenance_count": maintenance_count,
        "condemned_count": condemned_count,
        "office_labels": office_labels,
        "office_counts": office_counts,
        "status_labels": status_labels,
        "status_counts": status_counts,
        "recent_inventory": recent_inventory
    }

    return render(request, "inventory/dashboard.html", context)


# Export filtered inventory
def export_inventory_search_csv(request):
    inventories, _query = _inventory_search_queryset(request)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory_search.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Control Number",
            "User Name",
            "Computer Name",
            "Assigned IP",
            "Office",
            "Status",
        ]
    )

    for item in inventories:
        writer.writerow(
            [
                item.control_number,
                item.user_name,
                item.computer_name,
                item.assigned_ip,
                item.office_or_hospital,
                item.status,
            ]
        )

    return response


def export_inventory_search_excel(request):
    inventories, _query = _inventory_search_queryset(request)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inventory Search"

    sheet.append(
        [
            "Control Number",
            "User Name",
            "Computer Name",
            "Assigned IP",
            "Office",
            "Status",
        ]
    )

    for item in inventories:
        sheet.append(
            [
                item.control_number,
                item.user_name,
                item.computer_name,
                item.assigned_ip,
                item.office_or_hospital,
                item.status,
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="inventory_search.xlsx"'

    workbook.save(response)

    return response


# 🔓 PUBLIC VIEW
def inventory_detail(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk)
    components = inventory.components.all()
    return render(request, 'inventory/inventory_detail.html', {
        'inventory': inventory,
        'components': components
    })


# 🔐 LOGIN REQUIRED
@login_required
def inventory_create(request):

    EquipmentFormSet = formset_factory(EquipmentStaticForm, extra=0)

    # Get component names directly from model choices
    equipment_list = [
        choice[0] for choice in EquipmentComponent.COMPONENT_CHOICES
    ]

    if request.method == "POST":
        form = InventoryForm(request.POST)
        formset = EquipmentFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            inventory = form.save()

            # Optional: Save components
            for form_data in formset.cleaned_data:
                EquipmentComponent.objects.create(
                    inventory=inventory,
                    component_name=form_data["equipment_name"],
                    original_model=form_data.get("original_model", ""),
                    original_serial=form_data.get("original_serial", ""),
                   # replacement_model=form_data.get("replacement_model", ""),
                   # replacement_serial=form_data.get("replacement_serial", ""),
                    remarks=form_data.get("remarks", "")
                )

            return redirect("inventory:inventory_list")

    else:
        form = InventoryForm()

        initial_data = [
            {"equipment_name": name}
            for name in equipment_list
        ]

        formset = EquipmentFormSet(initial=initial_data)

    return render(request, "inventory/inventory_form.html", {
        "form": form,
        "formset": formset
    })

# 🔐 LOGIN REQUIRED
@login_required
def inventory_update(request, pk):

    inventory = get_object_or_404(Inventory, pk=pk)

    EquipmentFormSet = formset_factory(EquipmentStaticForm, extra=0)

    equipment_list = [choice[0] for choice in EquipmentComponent.COMPONENT_CHOICES]

    if request.method == "POST":

        form = InventoryForm(request.POST, instance=inventory)
        formset = EquipmentFormSet(request.POST)

        if form.is_valid() and formset.is_valid():

            form.save()

            # remove old components
            inventory.components.all().delete()

            for form_data in formset.cleaned_data:

                if form_data:

                    EquipmentComponent.objects.create(
                        inventory=inventory,
                        component_name=form_data["equipment_name"],
                        original_model=form_data.get("original_model", ""),
                        original_serial=form_data.get("original_serial", ""),
                        replacement_model=form_data.get("replacement_model", ""),
                        replacement_serial=form_data.get("replacement_serial", ""),
                        remarks=form_data.get("remarks", "")
                    )

            return redirect("inventory:inventory_list")

    else:

        form = InventoryForm(instance=inventory)

        components = inventory.components.all()

        initial_data = []

        for name in equipment_list:

            component = components.filter(component_name=name).first()

            if component:
                initial_data.append({
                    "equipment_name": name,
                    "original_model": component.original_model,
                    "original_serial": component.original_serial,
                    "replacement_model": component.replacement_model,
                    "replacement_serial": component.replacement_serial,
                    "remarks": component.remarks
                })
            else:
                initial_data.append({
                    "equipment_name": name
                })

        formset = EquipmentFormSet(initial=initial_data)

    return render(request, "inventory/inventory_form.html", {
        "form": form,
        "formset": formset
    })


# 🔐 LOGIN + DELETE PERMISSION REQUIRED
@permission_required('inventory.delete_inventory', raise_exception=True)
def inventory_delete(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk)

    if request.method == "POST":
        inventory.delete()
        return redirect('inventory:inventory_list')

    return render(request, 'inventory/inventory_delete.html', {
        'inventory': inventory
    })
