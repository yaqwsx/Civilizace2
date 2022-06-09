# Generated by Django 4.0.5 on 2022-06-09 12:02

import core.models.fields
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields
import game.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DbAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actionType', models.CharField(max_length=64, verbose_name='actionType')),
                ('entitiesRevision', models.IntegerField()),
                ('description', models.TextField(null=True)),
                ('args', core.models.fields.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='DbEntities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField(verbose_name='data')),
            ],
            options={
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='DbInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='Time of creating the action')),
                ('phase', enumfields.fields.EnumField(enum=game.models.InteractionType, max_length=10)),
                ('workConsumed', models.IntegerField(default=0)),
                ('actionObject', core.models.fields.JSONField()),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='game.dbaction')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DbMapState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField(verbose_name='data')),
            ],
        ),
        migrations.CreateModel(
            name='DbTask',
            fields=[
                ('id', models.CharField(max_length=32, primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('capacity', models.IntegerField()),
                ('orgDescription', models.TextField()),
                ('teamDescription', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='DbTick',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('lastTick', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='DbTurn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('startedAt', models.DateTimeField(null=True)),
                ('enabled', models.BooleanField(default=False)),
                ('duration', models.IntegerField(default=900, validators=[django.core.validators.MinValueValidator(0)])),
            ],
            options={
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='DbWorldState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField(verbose_name='data')),
            ],
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=200)),
                ('port', models.IntegerField()),
                ('registeredAt', models.DateTimeField(auto_now=True)),
                ('printsStickers', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='DbTeamState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField(verbose_name='data')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.team')),
            ],
        ),
        migrations.CreateModel(
            name='DbTaskPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('techId', models.CharField(max_length=32)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='techs', to='game.dbtask')),
            ],
        ),
        migrations.CreateModel(
            name='DbTaskAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('techId', models.CharField(max_length=32)),
                ('assignedAt', models.DateTimeField(auto_now=True)),
                ('finishedAt', models.DateTimeField(null=True)),
                ('abandoned', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='game.dbtask')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.team')),
            ],
        ),
        migrations.CreateModel(
            name='DbSticker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entityId', models.CharField(max_length=32)),
                ('entityRevision', models.IntegerField()),
                ('type', models.IntegerField(choices=[(0, 'Regular'), (1, 'Techsmall'), (2, 'Techfirst')])),
                ('awardedAt', models.DateTimeField(auto_now=True)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stickers', to='core.team')),
            ],
        ),
        migrations.CreateModel(
            name='DbState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='game.dbinteraction')),
                ('mapState', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbmapstate')),
                ('teamStates', models.ManyToManyField(to='game.dbteamstate')),
                ('worldState', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbworldstate')),
            ],
            options={
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='DbDelayedEffect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=8)),
                ('round', models.IntegerField()),
                ('target', models.IntegerField()),
                ('stickers', core.models.fields.JSONField(null=True)),
                ('performed', models.BooleanField(default=False)),
                ('withdrawn', models.BooleanField(default=False)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbaction')),
                ('team', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to='core.team')),
            ],
        ),
        migrations.AddConstraint(
            model_name='dbtaskpreference',
            constraint=models.UniqueConstraint(fields=('task', 'techId'), name='unique_preference'),
        ),
    ]
