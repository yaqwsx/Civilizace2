# Generated by Django 3.0 on 2019-12-13 09:57

from django.db import migrations, models
import django.db.models.deletion
import django_enumfield.db.fields
import game.models.action
import game.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='Time of creating the action')),
                ('move', django_enumfield.db.fields.EnumField(enum=game.models.action.ActionMove)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PopulationTeamState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True, verbose_name='Name')),
            ],
            options={
                'permissions': (('stat_team', 'Can view stats for the team'), ('play_team', 'Can play for the team')),
            },
        ),
        migrations.CreateModel(
            name='WealthTeamState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorldState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TeamState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('population', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.PopulationTeamState')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
                ('wealth', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.WealthTeamState')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Action')),
                ('teamStates', models.ManyToManyField(to='game.TeamState')),
                ('worldState', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.WorldState')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='action',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.Team'),
        ),
    ]
