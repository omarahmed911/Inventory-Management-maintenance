from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from ..permissions import permission_required, has_permission
from ..models import UserProfile, Role, Permission, PasswordChangeRequest, Activity
from ..serializers import UserSerializer, CreateUserSerializer

User = get_user_model()


@api_view(["POST"])
@permission_required("users", "create")
def create_user(request):
    serializer = CreateUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        role_name = request.data.get("role", "Employee")
        role_obj = Role.objects.filter(name=role_name).first()
        if role_obj:
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

        Activity.objects.create(action="Create User", user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_required("users", "view")
def get_users(request):
    users = User.objects.select_related("userprofile").prefetch_related("permissions").all()
    serializer = UserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_required("users", "view")
def get_single_user(request, pk):
    try:
        user = User.objects.select_related("userprofile").get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    is_owner = hasattr(request.user, "userprofile") and request.user.userprofile.role == "Owner"
    is_admin = is_owner or has_permission(request.user, "users", "update")
    is_self = request.user.id == user.id

    if not (is_self or is_admin):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    if "role" in request.data and not is_admin:
        return Response({"error": "Permission denied to change role"}, status=status.HTTP_403_FORBIDDEN)

    password_changed = False
    user.first_name = request.data.get("first_name", user.first_name)
    user.email = request.data.get("email", user.email)
    old_password = request.data.get("old_password")
    password1 = request.data.get("password1")
    password2 = request.data.get("password2")

    if old_password or password1 or password2:
        if not old_password:
            return Response({"old_password": "Old password required"}, status=400)

        if not user.check_password(old_password):
            return Response({"old_password": "Old password incorrect"}, status=400)

        if password1 != password2:
            return Response({"password": "Passwords do not match"}, status=400)

        user.set_password(password1)
        password_changed = True

        PasswordChangeRequest.objects.filter(
            user=user,
            status="Approved"
        ).update(status="Completed")
    user.save()
    profile = user.userprofile
    profile.phone = request.data.get("phone", profile.phone)
    if is_admin and "role" in request.data:
        profile.role = request.data.get("role", profile.role)

    if request.FILES.get("profile_image"):
        profile.profile_image = request.FILES.get("profile_image")

    profile.save()
    Activity.objects.create(action="Update User", user=request.user)
    return Response({
        "message": "User updated successfully",
        "password_changed": password_changed
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_old_password(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    is_owner = hasattr(request.user, "userprofile") and request.user.userprofile.role == "Owner"
    is_admin = is_owner or has_permission(request.user, "users", "update")
    if request.user.id != user.id and not is_admin:
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    old_password = request.data.get("old_password")

    if not old_password:
        return Response({"old_password": "Old password required"}, status=400)

    if not user.check_password(old_password):
        return Response({"old_password": "Old password is incorrect"}, status=400)
    return Response({"message": "Password verified"})


@api_view(["PATCH"])
@permission_required("users", "update")
def toggle_user_status(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    user.is_active = not user.is_active
    user.save()
    return Response({"is_active": user.is_active})


@api_view(["DELETE"])
@permission_required("users", "delete")
def delete_user(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    user.delete()
    return Response({"message": "User deleted successfully"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_password_change(request):
    existing = PasswordChangeRequest.objects.filter(
        user=request.user,
        status__in=["Pending", "Approved"]
    ).exists()

    if existing:
        return Response({"error": "Request already pending"}, status=400)

    PasswordChangeRequest.objects.create(user=request.user)
    return Response({"message": "Password change request sent"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_password_requests(request):
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Permission denied"}, status=403)

    requests = PasswordChangeRequest.objects.select_related("user").all().order_by("-created_at")
    data = [
        {
            "id": r.id,
            "username": r.user.username,
            "name": r.user.first_name,
            "status": r.status,
            "request_type": r.request_type,
            "message": r.message,
            "created_at": r.created_at
        }
        for r in requests
    ]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_password_request(request, pk):
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Permission denied"}, status=403)

    req = get_object_or_404(PasswordChangeRequest, pk=pk)

    if req.status != "Pending":
        return Response({"error": "Already processed"}, status=400)

    req.status = "Approved"
    req.save()
    return Response({"message": "Request approved"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def decline_password_request(request, pk):
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Permission denied"}, status=403)

    req = get_object_or_404(PasswordChangeRequest, pk=pk)
    req.status = "Rejected"
    req.save()
    return Response({"message": "Request declined"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_password_request_status(request):
    approved_request = PasswordChangeRequest.objects.filter(
        user=request.user,
        status="Approved"
    ).exists()
    return Response({
        "approved": approved_request
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def request_account_resume(request):
    """Paused user sends an account resume request from the login page."""
    username = request.data.get("username")
    message = request.data.get("message", "")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    if user.is_active:
        return Response({"error": "Account is already active"}, status=400)

    existing = PasswordChangeRequest.objects.filter(
        user=user,
        request_type="account_resume",
        status="Pending"
    ).exists()

    if existing:
        return Response({"error": "Request already pending"}, status=400)

    PasswordChangeRequest.objects.create(
        user=user,
        request_type="account_resume",
        message=message,
        status="Pending",
    )
    return Response(
        {"message": "Resume request sent to owner. You will be able to log in once approved."},
        status=201
    )


@api_view(["POST"])
@permission_required("users", "update")
def resume_account(request, pk):
    """Owner approves resume request → reactivates user and marks request completed."""
    if request.user.userprofile.role != "Owner":
        return Response({"error": "Only Owner can resume accounts"}, status=403)

    req = get_object_or_404(PasswordChangeRequest, pk=pk, request_type="account_resume")

    if req.status != "Pending":
        return Response({"error": "Request is not pending"}, status=400)

    target_user = req.user
    target_user.is_active = True
    target_user.save()

    req.status = "Completed"
    req.save()

    Activity.objects.create(
        action=f"Resumed account for user: {target_user.username}",
        user=request.user
    )
    return Response({"message": f"Account for '{target_user.username}' has been reactivated."})
