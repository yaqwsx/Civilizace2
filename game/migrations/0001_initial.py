# Generated by Django 3.0.6 on 2021-06-15 22:19

import datetime
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django.utils.timezone
import django_enumfield.db.fields
import game.data.entity
import game.models.actionBase
import game.models.actionTypeList
import game.models.fields
import game.models.messageBoard
import game.models.state
import game.models.stickers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ground', '0001_initial'),
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('move', django_enumfield.db.fields.EnumField(enum=game.models.actionTypeList.ActionType)),
                ('arguments', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ActionEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='Time of creating the action')),
                ('phase', django_enumfield.db.fields.EnumField(enum=game.models.actionBase.ActionPhase)),
                ('workConsumed', models.IntegerField()),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Action')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('codeRevision', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='ground.GitRevision')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AssignedTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('techId', models.CharField(max_length=32)),
                ('assignedAt', models.DateTimeField()),
                ('completedAt', models.DateTimeField(default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DistanceItemBuilding',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DistanceLogger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('building', game.models.fields.ListField(model_type=game.models.state.DistanceItemBuilding)),
                ('teams', game.models.fields.ListField(model_type=game.models.state.DistanceItemTeams)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EnhancerInputModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
            ],
        ),
        migrations.CreateModel(
            name='EnhancerStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EntitiesVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='EntityModel',
            fields=[
                ('syntheticId', models.AutoField(primary_key=True, serialize=False)),
                ('id', models.CharField(max_length=20)),
                ('label', models.CharField(max_length=50)),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
            ],
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='ExpectedGeneration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generationDue', models.DateTimeField(default=None, null=True)),
                ('fulfilled', models.BooleanField(default=False)),
                ('seq', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='FoodStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FoodStorageItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenerationTickSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.DurationField(default=datetime.timedelta(seconds=900), null=True)),
                ('renew', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='IslandState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('islandId', models.CharField(max_length=32)),
                ('defense', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MaterialStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appearDateTime', models.DateTimeField(verbose_name='Time of appearance the message')),
                ('type', django_enumfield.db.fields.EnumField(enum=game.models.messageBoard.MessageType)),
                ('content', models.TextField(verbose_name='Message content')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PopulationTeamState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('population', models.IntegerField(verbose_name='population')),
                ('work', models.IntegerField(verbose_name='work')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Printer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=200)),
                ('registeredAt', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='ResourceStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SandboxTeamState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parameters', game.models.fields.JSONField()),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.ActionEvent')),
                ('islandStates', models.ManyToManyField(to='game.IslandState')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaskModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('teamDescription', models.TextField()),
                ('orgDescription', models.TextField()),
                ('capacity', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.CharField(max_length=32, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('color', models.CharField(max_length=20, verbose_name='Color')),
                ('assignedTasks', models.ManyToManyField(through='game.AssignedTask', to='game.TaskModel')),
            ],
            options={
                'permissions': (('stat_team', 'Can view stats for the team'), ('play_team', 'Can play for the team')),
            },
        ),
        migrations.CreateModel(
            name='TeamAchievements',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('list', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TechStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.JSONField()),
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
                ('generation', models.IntegerField()),
                ('foodValue', models.IntegerField()),
                ('castes', models.TextField()),
                ('storageLimit', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AchievementModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('implementation', models.CharField(max_length=50)),
                ('icon', models.CharField(max_length=50)),
                ('orgMessage', models.CharField(max_length=2028)),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='DieModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='EnhancerModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('flavour', models.TextField()),
                ('detail', models.TextField()),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('dots', models.IntegerField()),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='IslandModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('direction', django_enumfield.db.fields.EnumField(enum=game.data.entity.Direction)),
                ('distance', models.IntegerField()),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='ResourceModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('icon', models.CharField(max_length=30)),
                ('level', models.IntegerField(validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(6)])),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='ResourceTypeModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('color', models.CharField(max_length=7)),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='TechModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('culture', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('flavour', models.TextField()),
                ('notes', models.TextField()),
                ('image', models.TextField()),
                ('nodeTag', models.TextField()),
                ('epocha', models.IntegerField()),
                ('defenseBonus', models.IntegerField()),
                ('island', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='techs', to='game.IslandModel')),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='TeamState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turn', models.IntegerField()),
                ('discoveredIslandsList', game.models.fields.JSONField()),
                ('exploredIslandsList', game.models.fields.JSONField()),
                ('achievements', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.TeamAchievements')),
                ('distances', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.DistanceLogger')),
                ('enhancers', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='enhancers', to='game.EnhancerStorage')),
                ('foodSupply', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.FoodStorage')),
                ('materials', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='materials', to='game.MaterialStorage')),
                ('population', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.PopulationTeamState')),
                ('resources', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='resources', to='game.ResourceStorage')),
                ('sandbox', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.SandboxTeamState')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
                ('techs', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='techs', to='game.TechStorage')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaskMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('techId', models.CharField(max_length=32)),
                ('active', models.BooleanField(default=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.TaskModel')),
            ],
        ),
        migrations.CreateModel(
            name='Sticker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', django_enumfield.db.fields.EnumField(default=0, enum=game.models.stickers.StickerType)),
                ('awardedAt', models.DateTimeField(auto_now=True, verbose_name='Time of creating the action')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.EntityModel')),
                ('state', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.State')),
                ('team', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
            ],
        ),
        migrations.AddField(
            model_name='state',
            name='teamStates',
            field=models.ManyToManyField(to='game.TeamState'),
        ),
        migrations.AddField(
            model_name='state',
            name='worldState',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.WorldState'),
        ),
        migrations.CreateModel(
            name='MessageStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visible', models.BooleanField()),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Message')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
            ],
        ),
        migrations.CreateModel(
            name='MessageRead',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Message')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='islandstate',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='owened_islands', to='game.Team'),
        ),
        migrations.AddField(
            model_name='islandstate',
            name='techs',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.TechStorage'),
        ),
        migrations.CreateModel(
            name='DistanceItemTeams',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance', models.IntegerField()),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='assignedtask',
            name='task',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.TaskModel'),
        ),
        migrations.AddField(
            model_name='assignedtask',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team'),
        ),
        migrations.AddField(
            model_name='action',
            name='entitiesVersion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.EntitiesVersion'),
        ),
        migrations.AddField(
            model_name='action',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.Team'),
        ),
        migrations.CreateModel(
            name='AddStickerMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='CreateInitialMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='EnhancerMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='FinishResearchMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='FinishTaskMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='FoodSupplyMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='GodMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandAttackMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandColonizeMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandDiscoverMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandExploreMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandRepairMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandResearchMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandShareMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='IslandTransferMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='NextGenerationAction',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='NextTurn',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='ResearchMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='SandboxIncreaseCounterMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='SandboxMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='SpendWorkMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='StartRoundMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='StartTaskMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='TradeMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='VyrobaMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='WithdrawMove',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('game.action',),
        ),
        migrations.CreateModel(
            name='VyrobaModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('flavour', models.TextField()),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('dots', models.IntegerField()),
                ('build', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='building_vyrobas', to='game.TechModel')),
                ('die', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.DieModel')),
                ('output', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='output_of_vyroba', to='game.ResourceModel')),
                ('tech', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlock_vyrobas', to='game.TechModel')),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='VyrobaInputModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='game.VyrobaModel')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='input_to_vyrobas', to='game.ResourceModel')),
            ],
        ),
        migrations.CreateModel(
            name='TechEdgeModel',
            fields=[
                ('entitymodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='game.EntityModel')),
                ('dots', models.IntegerField()),
                ('die', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.DieModel')),
                ('dst', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocked_by', to='game.TechModel')),
                ('src', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocks_tech', to='game.TechModel')),
            ],
            bases=('game.entitymodel',),
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='TechEdgeInputModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='game.TechEdgeModel')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.ResourceModel')),
            ],
        ),
        migrations.AddConstraint(
            model_name='taskmapping',
            constraint=models.UniqueConstraint(fields=('task', 'techId'), name='taskmapping_pk'),
        ),
        migrations.AddField(
            model_name='resourcemodel',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='game.ResourceTypeModel'),
        ),
        migrations.AddField(
            model_name='islandmodel',
            name='root',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='game.TechModel'),
        ),
        migrations.AddField(
            model_name='foodstorageitem',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.ResourceModel'),
        ),
        migrations.AlterUniqueTogether(
            name='entitymodel',
            unique_together={('id', 'version')},
        ),
        migrations.AddField(
            model_name='enhancermodel',
            name='die',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.DieModel'),
        ),
        migrations.AddField(
            model_name='enhancermodel',
            name='tech',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlock_enhancers', to='game.TechModel'),
        ),
        migrations.AddField(
            model_name='enhancermodel',
            name='vyroba',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vyroba_enhancer', to='game.VyrobaModel'),
        ),
        migrations.AddField(
            model_name='enhancerinputmodel',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='game.EnhancerModel'),
        ),
        migrations.AddField(
            model_name='enhancerinputmodel',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='input_to_enhancements', to='game.ResourceModel'),
        ),
        migrations.AddField(
            model_name='distanceitembuilding',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='distance_source', to='game.TechModel'),
        ),
        migrations.AddField(
            model_name='distanceitembuilding',
            name='target',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='distance_target', to='game.TechModel'),
        ),
        migrations.AddConstraint(
            model_name='assignedtask',
            constraint=models.UniqueConstraint(fields=('task', 'team'), name='assignedtask_team-task'),
        ),
        migrations.AddConstraint(
            model_name='assignedtask',
            constraint=models.UniqueConstraint(fields=('techId', 'team'), name='assignedtask_team-tech'),
        ),
    ]
