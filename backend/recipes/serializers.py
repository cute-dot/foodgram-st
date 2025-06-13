from rest_framework import serializers
from .models import Recipe, Ingredient, IngredientInRecipe, Tag
from .fields import Base64ImageField


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ингредиент не существует.")
        return value


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'text', 'cooking_time', 'image',
            'ingredients', 'tags', 'is_favorited', 'is_in_shopping_cart'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated and
            obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated and
            obj.in_cart.filter(user=request.user).exists()
        )


class RecipeCreateSerializer(RecipeSerializer):
    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Ингредиенты обязательны.")
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Теги обязательны.")
        return value

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError("Время готовки должно быть больше 0.")
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Изображение обязательно.")
        return value

    def validate_text(self, value):
        if not value:
            raise serializers.ValidationError("Описание обязательно.")
        return value

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Название обязательно.")
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags_data:
            instance.tags.set(tags_data)
        if ingredients_data:
            instance.ingredients.clear()
            for ingredient_data in ingredients_data:
                IngredientInRecipe.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
        return instance