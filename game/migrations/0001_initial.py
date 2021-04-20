# Generated by Django 3.0.6 on 2021-04-20 18:59

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_enumfield.db.fields
import game.data.entity
import game.models.actionBase
import game.models.actionTypeList
import game.models.fields
import game.models.state


class Migration(migrations.Migration):

    initial = True

    dependencies = [
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
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DieModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
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
            name='EntitiesVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='FoodStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.ListField(model_type=game.models.state.FoodStorageItem)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenerationTick',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('running', models.BooleanField(default=False)),
                ('period', models.IntegerField(default=900)),
                ('forceUpdate', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='MaterialStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.ListField(model_type=game.models.state.ResourceStorageItem)),
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
            name='ResourceModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('icon', models.CharField(max_length=30)),
                ('level', models.IntegerField(validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(6)])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResourceStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.ListField(model_type=game.models.state.ResourceStorageItem)),
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
            name='TaskModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('popis', models.CharField(max_length=100)),
                ('text', models.TextField()),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('color', models.CharField(max_length=20, verbose_name='Color')),
            ],
            options={
                'permissions': (('stat_team', 'Can view stats for the team'), ('play_team', 'Can play for the team')),
            },
        ),
        migrations.CreateModel(
            name='TeamAchievements',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('list', game.models.fields.ListField(model_type=game.data.entity.AchievementModel)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TechModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('culture', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('flavour', models.TextField()),
                ('notes', models.TextField()),
                ('image', models.TextField()),
                ('nodeTag', models.TextField()),
                ('epocha', models.IntegerField()),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.TaskModel')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TechStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.ListField(model_type=game.models.state.TechStorageItem)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VlivStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', game.models.fields.ListField(model_type=game.models.state.VlivStorageItem)),
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
            name='VyrobaModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('flavour', models.TextField()),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('dots', models.IntegerField()),
                ('build', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='building_vyrobas', to='game.TechModel')),
                ('die', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.DieModel')),
                ('output', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='output_of_vyroba', to='game.ResourceModel')),
                ('tech', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlock_vyrobas', to='game.TechModel')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
            ],
            options={
                'abstract': False,
            },
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
            name='VlivStorageItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(default=0)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TechStorageItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', django_enumfield.db.fields.EnumField(enum=game.models.state.TechStatusEnum)),
                ('tech', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.TechModel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TechEdgeModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('dots', models.IntegerField()),
                ('die', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.DieModel')),
                ('dst', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocked_by', to='game.TechModel')),
                ('src', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocks_tech', to='game.TechModel')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
            ],
            options={
                'abstract': False,
            },
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
        migrations.CreateModel(
            name='TeamState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turn', models.IntegerField()),
                ('achievements', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.TeamAchievements')),
                ('distances', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.DistanceLogger')),
                ('foodSupply', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.FoodStorage')),
                ('materials', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.MaterialStorage')),
                ('population', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.PopulationTeamState')),
                ('resources', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.ResourceStorage')),
                ('sandbox', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.SandboxTeamState')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
                ('techs', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.TechStorage')),
                ('vliv', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.VlivStorage')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.ActionEvent')),
                ('teamStates', models.ManyToManyField(to='game.TeamState')),
                ('worldState', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.WorldState')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResourceTypeModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=7)),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResourceStorageItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.ResourceModel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='resourcemodel',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='game.ResourceTypeModel'),
        ),
        migrations.AddField(
            model_name='resourcemodel',
            name='version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion'),
        ),
        migrations.CreateModel(
            name='MessageStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visible', models.BooleanField()),
                ('read', models.BooleanField(default=False)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Message')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
            ],
        ),
        migrations.CreateModel(
            name='IslandModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
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
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.ResourceModel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EnhancementModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('amount', models.IntegerField()),
                ('tech', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlock_enhancers', to='game.TechModel')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
                ('vyroba', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enhancers', to='game.VyrobaModel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EnhancementInputModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='game.EnhancementModel')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='input_to_enhancements', to='game.ResourceModel')),
            ],
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
        migrations.CreateModel(
            name='DistanceItemBuilding',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance', models.IntegerField()),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='distance_source', to='game.TechModel')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='distance_target', to='game.TechModel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='diemodel',
            name='version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion'),
        ),
        migrations.AddField(
            model_name='action',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.Team'),
        ),
        migrations.CreateModel(
            name='AchievementModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('implementation', models.CharField(max_length=50)),
                ('icon', models.CharField(max_length=50)),
                ('orgMessage', models.CharField(max_length=2028)),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.EntitiesVersion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AddWonderMove',
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
            name='AttackMove',
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
            name='SetBuildingDistanceMove',
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
            name='SetTeamDistanceMove',
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
        migrations.AddConstraint(
            model_name='vyrobamodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='vyrobamodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='techmodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='techmodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='techedgemodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='techedgemodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='taskmodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='taskmodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='resourcetypemodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='resourcetypemodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='resourcemodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='resourcemodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='islandmodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='islandmodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='enhancementmodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='enhancementmodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='diemodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='diemodel_pk'),
        ),
        migrations.AddConstraint(
            model_name='achievementmodel',
            constraint=models.UniqueConstraint(fields=('id', 'version'), name='achievementmodel_pk'),
        ),
    ]
