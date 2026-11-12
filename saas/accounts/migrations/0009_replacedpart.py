import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_deploymentrun'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReplacedPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part_type', models.CharField(choices=[('ram', 'Mémoire RAM'), ('storage', 'Disque (SSD/HDD)'), ('battery', 'Batterie'), ('screen', 'Écran'), ('keyboard', 'Clavier / pavé tactile'), ('motherboard', 'Carte mère'), ('power', 'Alimentation'), ('charger', 'Chargeur'), ('fan', 'Ventilateur / refroidissement'), ('other', 'Autre pièce')], max_length=16)),
                ('description', models.CharField(blank=True, max_length=160)),
                ('cost_xof', models.PositiveIntegerField(default=0, help_text="Montant de la pièce, déjà inclus dans le coût de l'intervention.")),
                ('warranty_until', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('intervention', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parts', to='accounts.repairintervention')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
