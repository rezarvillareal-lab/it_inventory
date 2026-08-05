import csv
from typing import Iterable, Iterator, Optional, Tuple
from urllib import request

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Q
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover
    Workbook = None
from .forms import InventoryForm
from .models import EquipmentComponent, Inventory, UserProfile


def _get_visible_inventory_queryset(request):
    if not request.user.is_authenticated:
        return Inventory.objects.none()

    if request.user.is_superuser or request.user.is_staff:
        return Inventory.objects.all()

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return Inventory.objects.none()

    office = (profile.office_or_hospital or "").strip()
    if not office:
        return Inventory.objects.none()

    return Inventory.objects.filter(office_or_hospital__iexact=office)


def _get_visible_inventory_or_404(request, pk):
    return get_object_or_404(_get_visible_inventory_queryset(request), pk=pk)


def _inventory_search_queryset(request):
    query = (request.GET.get("q") or "").strip()
    inventories = _get_visible_inventory_queryset(request).prefetch_related("components").order_by("-created_at")

    # Generic text query (searches common inventory fields and component fields)
    if query:
        inventories = inventories.filter(
            Q(control_number__icontains=query)
            | Q(user_name__icontains=query)
            | Q(computer_name__icontains=query)
            | Q(assigned_ip__icontains=query)
            | Q(office_or_hospital__icontains=query)
            | Q(status__icontains=query)
            | Q(components__component_name__icontains=query)
            | Q(components__original_model__icontains=query)
            | Q(components__original_serial__icontains=query)
            | Q(components__replacement_model__icontains=query)
            | Q(components__replacement_serial__icontains=query)
            | Q(components__remarks__icontains=query)
        ).distinct()

    # Additional structured filters (dropdowns)
    equipment = (request.GET.get("equipment") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    office_filter = (request.GET.get("office") or "").strip()

    if equipment:
        inventories = inventories.filter(
            Q(components__component_name__iexact=equipment)
            | Q(components__component_name__icontains=equipment)
        ).distinct()

    if status_filter:
        inventories = inventories.filter(status__iexact=status_filter)

    if office_filter:
        inventories = inventories.filter(office_or_hospital__iexact=office_filter)

    return inventories, query


def _iter_inventory_component_rows(
    inventories: Iterable[Inventory],
) -> Iterator[Tuple[Inventory, Optional[EquipmentComponent]]]:
    for inventory in inventories:
        components = list(inventory.components.all().order_by("component_name", "id"))
        if not components:
            yield inventory, None
            continue

        for component in components:
            yield inventory, component


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("inventory:inventory_list")
    return redirect("login")


def inventory_list(request):
    inventories, query = _inventory_search_queryset(request)

    # Build dropdown options
    visible = _get_visible_inventory_queryset(request)
    from .models import EquipmentComponent, Inventory as InventoryModel

    component_names = (
        EquipmentComponent.objects.filter(inventory__in=visible)
        .values_list("component_name", flat=True)
        .distinct()
        .order_by("component_name")
    )
    equipment_options = [
        {"value": component_name, "label": component_name}
        for component_name in component_names
    ]

    office_choices = (
        visible.values_list("office_or_hospital", flat=True).distinct().order_by("office_or_hospital")
    )

    status_choices = [s[0] for s in InventoryModel.Status.choices]

    context = {
        "inventories": inventories,
        "query": query,
        "component_names": list(component_names),
        "equipment_options": equipment_options,
        "office_choices": list(office_choices),
        "status_choices": status_choices,
        # Echo current filters so template can preselect
        "selected_equipment": request.GET.get("equipment", ""),
        "selected_status": request.GET.get("status", ""),
        "selected_office": request.GET.get("office", ""),
    }

    return render(request, "inventory/inventory_list.html", context)


def reports(request):

    visible_inventory = _get_visible_inventory_queryset(request)

    office_report = (
        visible_inventory
        .values("office_or_hospital")
        .annotate(total=Count("id"))
        .order_by("office_or_hospital")
    )

    status_report = (
        visible_inventory
        .values("status")
        .annotate(total=Count("id"))
    )

    context = {
        "office_report": office_report,
        "status_report": status_report,
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
        'Status',
        "Component",
        "Original Model",+
        "Original Serial",
        "Replacement Model",
        "Replacement Serial",
        "Remarks",
    ])

    inventories = Inventory.objects.all().prefetch_related("components").order_by("-created_at")

    for item, component in _iter_inventory_component_rows(inventories):
        writer.writerow([
            item.control_number,
            item.user_name,
            item.computer_name,
            item.assigned_ip,
            item.office_or_hospital,
            item.status,
            component.component_name if component else "",
            component.original_model if component else "",
            component.original_serial if component else "",
            component.replacement_model if component else "",
            component.replacement_serial if component else "",
            component.remarks if component else "",
        ])

    return response


def export_inventory_excel(request):

    if Workbook is None:
        return HttpResponse(
            "Excel export requires openpyxl. Install openpyxl to enable this feature.",
            status=500,
            content_type="text/plain",
        )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inventory Report"

    sheet.append([
        "Control Number",
        "User Name",
        "Computer Name",
        "Assigned IP",
        "Office",
        "Status",
        "Component",
        "Original Model",
        "Original Serial",
        "Replacement Model",
        "Replacement Serial",
        "Remarks",
    ])

    inventories = Inventory.objects.all().prefetch_related("components").order_by("-created_at")

    for item, component in _iter_inventory_component_rows(inventories):
        sheet.append([
            item.control_number,
            item.user_name,
            item.computer_name,
            item.assigned_ip,
            item.office_or_hospital,
            item.status,
            component.component_name if component else "",
            component.original_model if component else "",
            component.original_serial if component else "",
            component.replacement_model if component else "",
            component.replacement_serial if component else "",
            component.remarks if component else "",
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = 'attachment; filename="inventory_report.xlsx"'

    workbook.save(response)

    return response


# STATIC EQUIPMENT FORM (no dropdown)
class EquipmentStaticForm(forms.Form):
    equipment_name = forms.CharField(
        widget=forms.TextInput(attrs={"readonly": "readonly"})
    )
    original_model = forms.CharField(required=False)
    original_serial = forms.CharField(required=False)
    replacement_model = forms.CharField(required=False)
    replacement_serial = forms.CharField(required=False)
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 1}))


@login_required
def dashboard(request):

    visible_inventory = _get_visible_inventory_queryset(request).order_by("-created_at")

    total_computers = visible_inventory.count()

    active_count = visible_inventory.filter(status=Inventory.Status.ACTIVE).count()
    maintenance_count = visible_inventory.filter(status=Inventory.Status.MAINTENANCE).count()
    condemned_count = visible_inventory.filter(status=Inventory.Status.CONDEMNED).count()
    disposed_count = visible_inventory.filter(status=Inventory.Status.DISPOSED).count()

    equipment_queryset = EquipmentComponent.objects.filter(inventory__in=visible_inventory)
    total_equipment_components = equipment_queryset.count()
    equipment_breakdown = (
        equipment_queryset
        .values("component_name")
        .annotate(total=Count("id"))
        .order_by("-total", "component_name")
    )
    equipment_type_count = equipment_breakdown.count()
    top_equipment_breakdown = [
        {"component_name": item["component_name"], "count": item["total"]}
        for item in equipment_breakdown[:5]
    ]
    equipment_labels = [item["component_name"] for item in equipment_breakdown]
    equipment_counts = [item["total"] for item in equipment_breakdown]
    equipment_type_progress = min(100, max(12, equipment_type_count * 10))

    offices = (
        visible_inventory
        .values("office_or_hospital")
        .annotate(total=Count("id"))
        .order_by("office_or_hospital")
    )

    office_labels = [o["office_or_hospital"] for o in offices]
    office_counts = [o["total"] for o in offices]

    statuses = (
        visible_inventory
        .values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    status_labels = [s["status"] for s in statuses]
    status_counts = [s["total"] for s in statuses]

    recent_inventory = visible_inventory.order_by("-created_at")[:5]

    context = {
        "total_computers": total_computers,
        "active_count": active_count,
        "maintenance_count": maintenance_count,
        "condemned_count": condemned_count,
        "disposed_count": disposed_count,
        "total_equipment_components": total_equipment_components,
        "equipment_type_count": equipment_type_count,
        "top_equipment_breakdown": top_equipment_breakdown,
        "equipment_labels": equipment_labels,
        "equipment_counts": equipment_counts,
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
            "Component",
            "Original Model",
            "Original Serial",
            "Replacement Model",
            "Replacement Serial",
            "Remarks",
        ]
    )

    for item, component in _iter_inventory_component_rows(inventories):
        writer.writerow(
            [
                item.control_number,
                item.user_name,
                item.computer_name,
                item.assigned_ip,
                item.office_or_hospital,
                item.status,
                component.component_name if component else "",
                component.original_model if component else "",
                component.original_serial if component else "",
                component.replacement_model if component else "",
                component.replacement_serial if component else "",
                component.remarks if component else "",
            ]
        )

    return response


def export_inventory_search_excel(request):
    inventories, _query = _inventory_search_queryset(request)

    if Workbook is None:
        return HttpResponse(
            "Excel export requires openpyxl. Install openpyxl to enable this feature.",
            status=500,
            content_type="text/plain",
        )

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
            "Component",
            "Original Model",
            "Original Serial",
            "Replacement Model",
            "Replacement Serial",
            "Remarks",
        ]
    )

    for item, component in _iter_inventory_component_rows(inventories):
        sheet.append(
            [
                item.control_number,
                item.user_name,
                item.computer_name,
                item.assigned_ip,
                item.office_or_hospital,
                item.status,
                component.component_name if component else "",
                component.original_model if component else "",
                component.original_serial if component else "",
                component.replacement_model if component else "",
                component.replacement_serial if component else "",
                component.remarks if component else "",
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
    inventory = _get_visible_inventory_or_404(request, pk)
    components = inventory.components.all()
    return render(request, 'inventory/inventory_detail.html', {
        'inventory': inventory,
        'components': components
    })


def inventory_print(request, pk):
    inventory = _get_visible_inventory_or_404(request, pk)
    components = inventory.components.all().order_by("component_name", "id")
    return render(request, 'inventory/inventory_print.html', {
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
#@permission_required('inventory.delete_inventory', raise_exception=True)
@login_required
def inventory_delete(request, pk):

    if not request.user.has_perm('inventory.delete_inventory'):
        raise PermissionDenied("Access Denied: You do not have permission to delete inventory items.")
   
    inventory = get_object_or_404(Inventory, pk=pk)

    if request.method == "POST":
        inventory.delete()
        return redirect('inventory:inventory_list')

    return render(request, 'inventory/inventory_delete.html', {
        'inventory': inventory
    })

def custom_403_view(request, exception=None):
    return render(request, '403.html', {
        'error_message': str(exception) if exception else "Access Denied: You do not have permission to delete inventory items."
    }, status=403)