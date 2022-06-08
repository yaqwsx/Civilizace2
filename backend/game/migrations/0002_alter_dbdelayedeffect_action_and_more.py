# Generated by Django 4.0.5 on 2022-06-08 21:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbdelayedeffect',
            name='action',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbaction'),
        ),
        migrations.AlterField(
            model_name='dbinteraction',
            name='action',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='game.dbaction'),
        ),
        migrations.AlterField(
            model_name='dbinteraction',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='dbstate',
            name='interaction',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='game.dbinteraction'),
        ),
        migrations.AlterField(
            model_name='dbstate',
            name='mapState',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbmapstate'),
        ),
        migrations.AlterField(
            model_name='dbstate',
            name='worldState',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbworldstate'),
        ),
        migrations.AlterField(
            model_name='dbteamstate',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.team'),
        ),
    ]