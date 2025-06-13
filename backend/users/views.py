from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import CustomUser, Follow
from .serializers import CustomUserSerializer, CustomUserCreateSerializer, FollowSerializer
from .fields import Base64ImageField


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        methods=['get', 'post'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(CustomUser, pk=pk)
        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(
                user=request.user, author=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.create(user=request.user, author=author)
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not Follow.objects.filter(
            user=request.user, author=author
        ).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.filter(user=request.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        follows = Follow.objects.filter(user=request.user)
        serializer = FollowSerializer(
            follows, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'errors': 'Поле avatar обязательно'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            field = Base64ImageField()
            try:
                parsed_avatar = field.to_internal_value(avatar_data)
            except serializers.ValidationError as e:
                return Response(
                    {'errors': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.avatar = parsed_avatar
            request.user.save()
            return Response({'avatar': request.user.avatar.url})
        elif request.method == 'DELETE':
            if not request.user.avatar:
                return Response(
                    {'errors': 'Аватар не установлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.user.avatar.delete()
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)