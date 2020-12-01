# Generated by Django 3.1.3 on 2020-12-01 14:07
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EdemocraciaGA',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('start_date', models.DateField(db_index=True, verbose_name='start date')),
                ('end_date', models.DateField(db_index=True, verbose_name='end date')),
                ('data', models.JSONField(blank=True, null=True, verbose_name='data')),
                ('period', models.CharField(choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('semiannually', 'Semiannually'), ('yearly', 'Yearly'), ('all', 'All the time')], db_index=True, default='daily', max_length=200, verbose_name='period')),
            ],
            options={
                'unique_together': {('start_date', 'period')},
            },
        ),
        migrations.CreateModel(
            name='EdemocraciaAnalysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('start_date', models.DateField(db_index=True, verbose_name='start date')),
                ('end_date', models.DateField(db_index=True, verbose_name='end date')),
                ('data', models.JSONField(blank=True, null=True, verbose_name='data')),
                ('period', models.CharField(choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('semiannually', 'Semiannually'), ('yearly', 'Yearly'), ('all', 'All the time')], db_index=True, default='daily', max_length=200, verbose_name='period')),
            ],
            options={
                'unique_together': {('start_date', 'period')},
            },
        ),
    ]
