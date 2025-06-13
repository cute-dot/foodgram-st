from django_filters import rest_framework as filters
from .models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author']

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            print(f"Favorited filter: user={self.request.user}, value={value}")  # Отладка
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            print(f"Shopping cart filter: user={self.request.user}, value={value}")  # Отладка
            filtered_qs = queryset.filter(in_shopping_cart__user=self.request.user)
            print(f"Filtered recipes: {[r.id for r in filtered_qs]}")  # Отладка
            return filtered_qs
        return queryset