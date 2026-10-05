from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0011_comment_likes_postimage'),
        ('accounts', '0009_ban_block_privacy'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reason', models.CharField(
                    choices=[('spam', 'Спам'), ('inappropriate', 'Неприемлемый контент'), ('harassment', 'Оскорбление или травля'), ('other', 'Другое')],
                    max_length=50,
                )),
                ('detail', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[('pending', 'На рассмотрении'), ('resolved', 'Принята'), ('dismissed', 'Отклонена')],
                    default='pending', max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_reports_sent', to=settings.AUTH_USER_MODEL)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='posts.comment')),
            ],
            options={'ordering': ['created_at'], 'unique_together': {('reporter', 'comment')}},
        ),
    ]
