# Generated by Django 3.0 on 2020-05-17 20:37

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_enumfield.db.fields
import game.models.actionBase
import game.models.fields
import game.models.keywords


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
                ('move', django_enumfield.db.fields.EnumField(enum=game.models.actionBase.ActionMove)),
                ('arguments', game.models.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ActionStep',
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
            name='GameDataModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='GenerationWorldState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generation', models.IntegerField(verbose_name='generation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=30, verbose_name='Game Word')),
                ('description', models.CharField(max_length=150)),
                ('valueType', django_enumfield.db.fields.EnumField(enum=game.models.keywords.KeywordType)),
                ('value', models.IntegerField()),
            ],
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
                ('isProduction', models.BooleanField(default=False)),
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.GameDataModel')),
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
            name='StorageItem',
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
            name='StorageState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items', models.ManyToManyField(to='game.StorageItem')),
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
                ('text', models.TextField()),
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.GameDataModel')),
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
            name='TechModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('culture', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('flavour', models.TextField()),
                ('notes', models.TextField()),
                ('image', models.TextField()),
                ('nodeTag', models.TextField()),
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.GameDataModel')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.TaskModel')),
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
                ('generation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.GenerationWorldState')),
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
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.GameDataModel')),
                ('die', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.DieModel')),
                ('output', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.ResourceModel')),
                ('tech', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlock_vyrobas', to='game.TechModel')),
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
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.VyrobaModel')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.ResourceModel')),
            ],
        ),
        migrations.CreateModel(
            name='TechEdgeModel',
            fields=[
                ('id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
                ('dots', models.IntegerField()),
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.GameDataModel')),
                ('die', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.DieModel')),
                ('dst', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocked_by', to='game.TechModel')),
                ('src', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocks_tech', to='game.TechModel')),
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
                ('population', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.PopulationTeamState')),
                ('sandbox', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.SandboxTeamState')),
                ('storage', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.StorageState')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.Team')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='game.ActionStep')),
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
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.GameDataModel')),
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
        migrations.AddField(
            model_name='diemodel',
            name='data',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.GameDataModel'),
        ),
        migrations.AddField(
            model_name='action',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='game.Team'),
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
    ]
