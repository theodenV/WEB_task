from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0008_user_cover'),
    ]

    operations = [
        migrations.AddField(model_name='user', name='is_banned', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='user', name='ban_reason', field=models.TextField(blank=True)),
        migrations.AddField(model_name='user', name='is_private', field=models.BooleanField(default=False)),
        migrations.AddField(
            model_name='user', name='dm_privacy',
            field=models.CharField(
                choices=[('all', 'Все'), ('following', 'Подписчики'), ('none', 'Никто')],
                default='all', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='user', name='comment_privacy',
            field=models.CharField(
                choices=[('all', 'Все'), ('following', 'Подписчики'), ('none', 'Никто')],
                default='all', max_length=10,
            ),
        ),
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('blocker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocking', to=settings.AUTH_USER_MODEL)),
                ('blocked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('blocker', 'blocked')}},
        ),
        migrations.CreateModel(
            name='FollowRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_follow_requests', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_follow_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('from_user', 'to_user')}},
        ),
        migrations.CreateModel(
            name='UserReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('reason', models.CharField(
                    choices=[('spam', 'Спам'), ('inappropriate', 'Неприемлемый контент'), ('harassment', 'Оскорбление или травля'), ('fake', 'Фейковый аккаунт'), ('other', 'Другое')],
                    max_length=50,
                )),
                ('detail', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[('pending', 'На рассмотрении'), ('resolved', 'Принята'), ('dismissed', 'Отклонена')],
                    default='pending', max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_reports_sent', to=settings.AUTH_USER_MODEL)),
                ('reported_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['created_at'], 'unique_together': {('reporter', 'reported_user')}},
        ),
    ]
