import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к JSON-файлу')

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    Ingredient.objects.get_or_create(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )
            self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))