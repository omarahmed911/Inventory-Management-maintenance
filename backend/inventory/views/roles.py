from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model

from ..permissions import permission_required
from ..models import Role, RolePermission, Permission, Activity, UserProfile
from ..serializers import RoleSerializer

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_roles(request):
    roles = Role.objects.prefetch_related('default_permissions').all()
    serializer = RoleSerializer(roles, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_required("users", "create")
def create_role(request):
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Only Owner can create roles"}, status=403)
    name = request.data.get("name", "").strip()
    if not name:
        return Response({"error": "Role name cannot be empty"}, status=400)
    if Role.objects.filter(name__iexact=name).exists():
        return Response({"error": f"Role '{name}' already exists"}, status=400)

    role = Role.objects.create(name=name, is_system=False)

    permissions_data = request.data.get("permissions", {})
    for module, actions in permissions_data.items():
        rp = RolePermission.objects.create(
            role=role,
            module=module,
            can_view=actions.get("view", False),
            can_create=actions.get("create", False),
            can_update=actions.get("update", False),
            can_delete=actions.get("delete", False),
        )
        if module == "dashboard":
            rp.set_dashboard_fields_list(actions.get("fields", []))
            rp.save()

    Activity.objects.create(action=f"Create Role: {role.name}", user=request.user)
    serializer = RoleSerializer(role)
    return Response(serializer.data, status=201)


@api_view(["PUT"])
@permission_required("users", "update")
@transaction.atomic
def update_role_permissions(request, role_id):
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Only Owner can update role permissions"}, status=403)

    role = get_object_or_404(Role, pk=role_id)
    permissions_data = request.data.get("permissions", {})
    if not isinstance(permissions_data, dict):
        return Response({"error": "Permissions must be an object"}, status=status.HTTP_400_BAD_REQUEST)

    RolePermission.objects.filter(role=role).delete()
    for module, actions in permissions_data.items():
        if not isinstance(actions, dict):
            actions = {}
        rp = RolePermission.objects.create(
            role=role,
            module=module,
            can_view=actions.get("view", False),
            can_create=actions.get("create", False),
            can_update=actions.get("update", False),
            can_delete=actions.get("delete", False),
        )
        if module == "dashboard":
            rp.set_dashboard_fields_list(actions.get("fields", []))
            rp.save()

    users_with_role = User.objects.filter(userprofile__role=role.name)
    updated_users = 0
    for user in users_with_role:
        Permission.objects.filter(user=user).delete()
        for module, actions in permissions_data.items():
            if not isinstance(actions, dict):
                actions = {}
            perm = Permission.objects.create(
                user=user,
                module=module,
                can_view=actions.get("view", False),
                can_create=actions.get("create", False),
                can_update=actions.get("update", False),
                can_delete=actions.get("delete", False),
            )
            if module == "dashboard":
                perm.set_dashboard_fields_list(actions.get("fields", []))
                perm.save()
        updated_users += 1

    Activity.objects.create(action=f"Update Role Permissions: {role.name} ({updated_users} users updated)", user=request.user)
    serializer = RoleSerializer(role)
    return Response({"role": serializer.data, "updated_users": updated_users, "message": f"Role updated and applied to {updated_users} existing user(s)"})


@api_view(["DELETE"])
@permission_required("users", "delete")
def delete_role(request, role_id):
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Only Owner can delete roles"}, status=403)

    role = get_object_or_404(Role, pk=role_id)

    if role.is_system:
        return Response({"error": "System roles cannot be deleted"}, status=400)

    user_count = UserProfile.objects.filter(role=role.name).count()
    if user_count > 0:
        return Response(
            {"error": f"Cannot delete: {user_count} user(s) still have this role"},
            status=400
        )

    role_name = role.name
    role.delete()
    Activity.objects.create(action=f"Delete Role: {role_name}", user=request.user)
    return Response({"message": f"Role '{role_name}' deleted successfully"})


@api_view(["POST"])
@permission_required("users", "update")
def apply_role_defaults_to_user(request, user_id):
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Only Owner can reset permissions"}, status=403)

    user = get_object_or_404(User, pk=user_id)
    role_name = user.userprofile.role

    try:
        role_obj = Role.objects.get(name=role_name)
    except Role.DoesNotExist:
        return Response({"error": f"No role defaults found for '{role_name}'"}, status=404)

    Permission.objects.filter(user=user).delete()
    applied = []
    for rp in role_obj.default_permissions.all():
        perm = Permission.objects.create(
            user=user,
            module=rp.module,
            can_view=rp.can_view,
            can_create=rp.can_create,
            can_update=rp.can_update,
            can_delete=rp.can_delete,
        )
        if rp.module == "dashboard":
            perm.set_dashboard_fields_list(rp.get_dashboard_fields_list())
            perm.save()
        applied.append(rp.module)

    Activity.objects.create(
        action=f"Reset Permissions to Default: {user.username} ({role_name})",
        user=request.user
    )
    return Response({"message": f"Permissions reset to '{role_name}' defaults", "modules": applied})


@api_view(["GET", "PUT"])
@permission_required("users", "update")
def user_permissions(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == "GET":
        perms = Permission.objects.filter(user=user)
        result = {}
        for p in perms:
            entry = {
                "view": p.can_view,
                "create": p.can_create,
                "update": p.can_update,
                "delete": p.can_delete,
            }
            if p.module == "dashboard":
                entry["fields"] = p.get_dashboard_fields_list()
            result[p.module] = entry
        return Response(result)

    elif request.method == "PUT":
        data = request.data.get("permissions", {})

        for module, actions in data.items():
            perm, created = Permission.objects.get_or_create(
                user=user,
                module=module
            )
            perm.can_view = actions.get("view", False)
            perm.can_create = actions.get("create", False)
            perm.can_update = actions.get("update", False)
            perm.can_delete = actions.get("delete", False)

            if module == "dashboard":
                perm.set_dashboard_fields_list(actions.get("fields", []))

            perm.save()

        Activity.objects.create(
            action=f"Update Permissions: {user.username}",
            user=request.user
        )
        return Response({"message": "Permissions updated successfully"})
