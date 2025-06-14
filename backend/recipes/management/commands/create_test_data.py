import random
import io
from PIL import Image
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from recipes.models import Recipe, IngredientInRecipe, Ingredient, Favorite, ShoppingCart
from users.models import Follow

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовых пользователей и рецепты'

    def handle(self, *args, **kwargs):
        if Recipe.objects.filter(name__startswith='Тестовый рецепт').exists():
            self.stdout.write(self.style.WARNING('Тестовые данные уже существуют. Пропускаем создание.'))
            return

        self.stdout.write('Создание тестовых пользователей...')

        user_data = [
            {'username': 'test_chef', 'email': 'chef@example.com',
             'first_name': 'Иван', 'last_name': 'Поваров', 'password': 'chef12345'},
            {'username': 'food_lover', 'email': 'lover@example.com',
             'first_name': 'Мария', 'last_name': 'Гурманова', 'password': 'foodie678'},
            {'username': 'baking_pro', 'email': 'baker@example.com',
             'first_name': 'Алексей', 'last_name': 'Пекарев', 'password': 'bake9876'}
        ]

        users = []
        for data in user_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            if created:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Создан пользователь {user.username} (пароль: {data["password"]})')
                )
            users.append(user)

        ingredients = list(Ingredient.objects.all())
        if not ingredients:
            self.stdout.write(self.style.ERROR('Не найдены ингредиенты в базе. Сначала загрузите их.'))
            return

        self.stdout.write('Создание тестовых рецептов...')

        def create_test_image(color):
            image = Image.new('RGB', (800, 600), color=color)
            image_io = io.BytesIO()
            image.save(image_io, format='JPEG')
            return SimpleUploadedFile(
                name=f"test_{color[0]}_{color[1]}_{color[2]}.jpg",
                content=image_io.getvalue(),
                content_type="image/jpeg"
            )

        recipes = []
        for i, user in enumerate(users):
            color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200)
            )

            recipe = Recipe.objects.create(
                author=user,
                name=f'Тестовый рецепт {i + 1}',
                text=f'Это тестовый рецепт №{i + 1}, созданный автоматически. Подробное описание приготовления блюда.',
                cooking_time=random.randint(10, 120),
                image=create_test_image(color)
            )
            recipes.append(recipe)

            selected_ingredients = random.sample(ingredients, random.randint(3, 5))
            for ingredient in selected_ingredients:
                IngredientInRecipe.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=random.randint(1, 500)
                )

            self.stdout.write(
                self.style.SUCCESS(f'Создан рецепт "{recipe.name}" для пользователя {user.username}')
            )

        if len(users) >= 2:
            Follow.objects.get_or_create(user=users[0], author=users[1])
            Follow.objects.get_or_create(user=users[1], author=users[2])
            self.stdout.write(self.style.SUCCESS('Созданы тестовые подписки между пользователями'))

        if len(recipes) >= 2:
            Favorite.objects.get_or_create(user=users[0], recipe=recipes[0])
            Favorite.objects.get_or_create(user=users[1], recipe=recipes[1])
            ShoppingCart.objects.get_or_create(user=users[0], recipe=recipes[1])
            ShoppingCart.objects.get_or_create(user=users[1], recipe=recipes[2])
            self.stdout.write(self.style.SUCCESS('Добавлены тестовые данные в избранное и список покупок'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано:\n'
                f'- Пользователей: {len(users)}\n'
                f'- Рецептов: {len(recipes)}\n'
                f'- Связей рецепт-ингредиент: {IngredientInRecipe.objects.count()}\n'
                f'- Подписок: {Follow.objects.count()}\n'
                f'- Избранных рецептов: {Favorite.objects.count()}\n'
                f'- Рецептов в списке покупок: {ShoppingCart.objects.count()}'
            )
        )