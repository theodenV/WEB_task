from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_post_moderation_lock'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='rejection_reason',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.CreateModel(
            name='PostReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(
                    choices=[
                        ('spam', 'Спам'),
                        ('inappropriate', 'Неприемлемый контент'),
                        ('copyright', 'Нарушение авторских прав'),
                        ('harassment', 'Оскорбление или травля'),
                        ('other', 'Другое'),
                    ],
                    max_length=50,
                )),
                ('comment', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'На рассмотрении'),
                        ('resolved', 'Принята'),
                        ('dismissed', 'Отклонена'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reports',
                    to='posts.post',
                )),
                ('reporter', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reports_made',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['created_at'],
                'unique_together': {('reporter', 'post')},
            },
        ),
    ]
