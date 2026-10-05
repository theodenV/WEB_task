from django.core.management.base import BaseCommand  # базовый класс для кастомных management-команд Django
from posts.models import Post, PostColor  # модели поста и цвета поста (PostColor хранит доминирующий цвет изображения)
from posts.models import _extract_colors  # приватная функция извлечения цветов из изображения (использует Pillow)


class Command(BaseCommand):  # класс команды — Django находит его по имени файла: python manage.py extract_colors
    help = 'Extract dominant colors for all published posts that have no color data yet'  # описание команды в --help

    def handle(self, *args, **options):  # основной метод — вызывается при запуске команды
        qs = Post.objects.filter(  # QuerySet постов для обработки
            media_type='image',  # только посты с изображениями (не видео)
        ).exclude(image='')  # исключаем посты без загруженного файла изображения

        total = qs.count()  # общее количество постов для переиндексации
        self.stdout.write(f'Re-indexing {total} posts...')  # выводим прогресс в терминал

        done = 0  # счётчик успешно обработанных постов
        for post in qs.iterator():  # iterator(): не загружаем весь QuerySet в память, обрабатываем по одному
            if not post.image:  # дополнительная проверка (ImageField может быть не None, но пустым)
                continue  # пропускаем пост без изображения
            try:
                colors = _extract_colors(post.image.path)  # вызываем функцию: путь к файлу → список цветов [{hex, h, s, l}]
                PostColor.objects.filter(post=post).delete()  # удаляем старые данные о цветах этого поста
                if colors:  # если функция вернула хотя бы один цвет
                    PostColor.objects.bulk_create([  # bulk_create: вставляем все цвета одним SQL-запросом (эффективнее цикла)
                        PostColor(post=post, hex=c['hex'], hue=c['h'],  # создаём объект PostColor для каждого цвета
                                  saturation=c['s'], lightness=c['l'])  # hue/saturation/lightness — HSL-компоненты цвета
                        for c in colors  # генераторное выражение: создаём список объектов PostColor
                    ])
                    done += 1  # инкрементируем счётчик успеха
            except Exception as e:  # ловим любую ошибку (файл не найден, Pillow-ошибка и т.д.)
                self.stdout.write(f'  skip post#{post.id}: {e}')  # логируем ошибку и продолжаем (не прерываем цикл)

        self.stdout.write(self.style.SUCCESS(f'Done: {done}/{total} posts indexed'))  # итоговый вывод зелёным цветом
