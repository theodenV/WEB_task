from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0004_user_email_fields')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_token_created',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
