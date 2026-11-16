from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token

from ..serializers import UserSerializer

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    try:
        user_obj = User.objects.get(username=username)
        if not user_obj.is_active and user_obj.check_password(password):
            return Response(
                {
                    "error": "account_hold",
                    "message": "Your account has been put on hold. Please contact the owner to resume access."
                },
                status=status.HTTP_403_FORBIDDEN
            )
    except User.DoesNotExist:
        pass  # Fall through to authenticate() which will return None

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        serializer = UserSerializer(
            user,
            context={'request': request}
        )
        return Response(serializer.data)
    return Response(
        {"error": "Invalid username or password"},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"})


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_cookie(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)
