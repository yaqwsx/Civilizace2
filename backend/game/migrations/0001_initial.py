# Generated by Django 4.0.4 on 2022-05-30 22:20

import core.models.fields
from django.conf import settings
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
                ('args', core.models.fields.JSONField(verbose_name='data')),
                ('cost', core.models.fields.JSONField(verbose_name='cost')),
            ],
        ),
        migrations.CreateModel(
            name='DbEntities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField(verbose_name='data')),
            ],
        ),
        migrations.CreateModel(
            name='DbInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='Time of creating the action')),
                ('phase', enumfields.fields.EnumField(enum=game.models.InteractionType, max_length=10)),
                ('workConsumed', models.IntegerField(default=0)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='interactions', to='game.dbaction')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
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
            name='DbTeamState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField(verbose_name='data')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.team')),
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
            name='DbState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turn', models.IntegerField()),
                ('interaction', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.dbinteraction')),
                ('mapState', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.dbmapstate')),
                ('teamStates', models.ManyToManyField(to='game.dbteamstate')),
            ],
            options={
                'get_latest_by': 'id',
            },
        ),
        migrations.AddConstraint(
            model_name='dbtaskpreference',
            constraint=models.UniqueConstraint(fields=('task', 'techId'), name='unique_preference'),
        ),
        migrations.AddConstraint(
            model_name='dbtaskassignment',
            constraint=models.UniqueConstraint(fields=('team', 'task', 'techId'), name='unique_assignment'),
        ),
    ]
