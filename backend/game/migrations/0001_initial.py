import core.models.fields
import django.core.validators
import django.db.models.deletion
import django_enumfield.db.fields
import game.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DbAction',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('actionType', models.CharField(max_length=64)),
                ('entitiesRevision', models.IntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('args', core.models.fields.JSONField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DbEntities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField()),
            ],
            options={
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='DbMapDiff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
                ('type', django_enumfield.db.fields.EnumField(enum=game.models.DiffType)),
                ('tile', models.CharField(blank=True, max_length=32, null=True)),
                ('newRichness', models.IntegerField(blank=True, null=True)),
                ('newLevel', models.IntegerField(blank=True, null=True)),
                ('team', models.CharField(blank=True, max_length=32, null=True)),
                ('armyName', models.CharField(blank=True, max_length=32, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DbMapState',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('data', core.models.fields.JSONField()),
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
            name='DbTurn',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('startedAt', models.DateTimeField(blank=True, null=True)),
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
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('data', core.models.fields.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=200)),
                ('port', models.IntegerField()),
                ('registeredAt', models.DateTimeField(auto_now_add=True)),
                ('printsStickers', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='DbSticker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entityId', models.CharField(max_length=32)),
                ('entityRevision', models.IntegerField()),
                ('type', django_enumfield.db.fields.EnumField(enum=game.models.StickerType)),
                ('awardedAt', models.DateTimeField(auto_now_add=True)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stickers', to='core.team')),
            ],
        ),
        migrations.CreateModel(
            name='DbTaskAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('techId', models.CharField(max_length=32)),
                ('assignedAt', models.DateTimeField(auto_now_add=True)),
                ('finishedAt', models.DateTimeField(blank=True, null=True)),
                ('abandoned', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='assignments', to='game.dbtask')),
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
            name='DbTeamState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', core.models.fields.JSONField()),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.team')),
            ],
        ),
        migrations.CreateModel(
            name='DbScheduledAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('start_time_s', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('delay_s', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('performed', models.BooleanField(default=False)),
                ('action', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled', to='game.dbaction')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('created_from', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subsequent', to='game.dbaction')),
                ('start_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbturn')),
            ],
        ),
        migrations.CreateModel(
            name='DbState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mapState', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbmapstate')),
                ('teamStates', models.ManyToManyField(related_name='states', to='game.dbteamstate')),
                ('worldState', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.dbworldstate')),
            ],
            options={
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='DbInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Time of creating the action')),
                ('phase', django_enumfield.db.fields.EnumField(enum=game.models.InteractionType)),
                ('actionObject', core.models.fields.JSONField(blank=True)),
                ('trace', models.TextField(blank=True, default='')),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='game.dbaction')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('new_state', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='interaction', to='game.dbstate')),
            ],
            options={
                'unique_together': {('action', 'phase')},
            },
        ),
        migrations.AddConstraint(
            model_name='dbtaskassignment',
            constraint=models.UniqueConstraint(condition=models.Q(('abandoned', False)), fields=('team', 'techId'), name='Unique task assignment for each tech per team'),
        ),
        migrations.AddConstraint(
            model_name='dbtaskassignment',
            constraint=models.UniqueConstraint(condition=models.Q(('abandoned', False), ('finishedAt__isnull', False)), fields=('team', 'task'), name='Unique task per team'),
        ),
        migrations.AddConstraint(
            model_name='dbtaskpreference',
            constraint=models.UniqueConstraint(fields=('task', 'techId'), name='unique_preference'),
        ),
    ]
