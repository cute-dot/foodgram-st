from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum
from django.http import HttpResponse
from django.http import Http404
from .models import Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart, ShortLink
from .serializers import RecipeSerializer, RecipeCreateSerializer, RecipeMinifiedSerializer, IngredientSerializer
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
import shortuuid
import traceback


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend]

    def get_permissions(self):
        if self.action in ['create', 'favorite', 'shopping_cart']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def update(self, request, *args, **kwargs):
        print(f"Requested recipe ID: {kwargs.get('pk')}")
        print(f"Available recipes: {list(Recipe.objects.values_list('id', flat=True))}")
        return super().update(request, *args, **kwargs)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется аутентификация.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт не в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        print(f"Requested recipe ID: {pk}")
        try:
            recipe = Recipe.objects.get(pk=pk)
            print(f"Found recipe: {recipe.id}, {recipe.name}")
            short_link, created = ShortLink.objects.get_or_create(
                recipe=recipe,
                defaults={'short_code': shortuuid.uuid()[:8]}
            )
            url = request.build_absolute_uri(
                reverse('short-link-redirect', args=[short_link.short_code])
            )
            print(f"Generated short link: {url}")
            return Response({'short-link': url})
        except Recipe.DoesNotExist:
            print(f"Recipe with ID {pk} not found")
            return Response(
                {"detail": "Рецепт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error in get_link: {str(e)}")
            return Response(
                {"detail": "Ошибка при генерации ссылки"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется аутентификация.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт не в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        try:
            print(f"User: {request.user}")
            ingredients = IngredientInRecipe.objects.filter(
                recipe__in_shopping_cart__user=request.user
            ).values(
                'ingredient__name', 'ingredient__measurement_unit'
            ).annotate(
                total_amount=Sum('amount')
            )
            print(f"Ingredients: {list(ingredients)}")

            if not ingredients:
                return Response(
                    {"detail": "Список покупок пуст."},
                    status=status.HTTP_200_OK,
                    content_type='application/json'
                )

            content = "Список покупок\n\n"
            for item in ingredients:
                content += (
                    f"{item['ingredient__name']} - "
                    f"{item['total_amount']} {item['ingredient__measurement_unit']}\n"
                )

            response = HttpResponse(
                content_type='text/plain; charset=utf-8',
                content=content.encode('utf-8')
            )
            response['Content-Disposition'] = (
                'attachment; filename="shopping_cart.txt"'
            )
            return response

        except Exception as e:
            print(f"Error in download_shopping_cart: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {"detail": "Ошибка при генерации файла."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


def short_link_redirect(request, short_code):
    recipe = get_object_or_404(Recipe, id=short_code)
    return redirect(f'/recipes/{recipe.id}/')