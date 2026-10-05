from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_post_rejection_reason_postreport'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PostImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='post_images/')),
                ('order', models.PositiveIntegerField(default=0)),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='images',
                    to='posts.post',
                )),
            ],
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='comment',
            name='likes',
            field=models.ManyToManyField(
                blank=True,
                related_name='liked_comments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
