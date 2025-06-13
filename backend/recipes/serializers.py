from rest_framework import serializers
from .models import Recipe, Ingredient, IngredientInRecipe
from .fields import Base64ImageField
from users.serializers import CustomUserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ингредиент не существует.")
        return value


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(source='ingredientinrecipe_set', many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'name', 'text', 'cooking_time', 'image',
            'ingredients', 'is_favorited', 'is_in_shopping_cart'
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
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(min_value=1)
        ),
        write_only=True
    )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Ингредиенты обязательны.")
        seen_ids = set()
        for ingredient in value:
            ingredient_id = ingredient.get('id')
            if not ingredient_id:
                raise serializers.ValidationError("ID ингредиента обязателен.")
            if ingredient_id in seen_ids:
                raise serializers.ValidationError("Ингредиенты не должны повторяться.")
            seen_ids.add(ingredient_id)
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(f"Ингредиент с ID {ingredient_id} не существует.")
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
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if ingredients_data:
            instance.ingredients.clear()
            for ingredient_data in ingredients_data:
                IngredientInRecipe.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data