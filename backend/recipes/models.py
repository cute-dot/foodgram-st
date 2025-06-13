from django.db import models
from users.models import CustomUser


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='recipes')
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredient, through='IngredientInRecipe')
    cooking_time = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='in_cart')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='in_cart')

    class Meta:
        unique_together = ('user', 'recipe')


class ShortLink(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)
    short_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.short_code