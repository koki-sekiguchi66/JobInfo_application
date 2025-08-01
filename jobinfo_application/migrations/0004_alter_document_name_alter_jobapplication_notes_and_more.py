# Generated by Django 4.2.23 on 2025-07-26 05:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobinfo_application', '0003_jobtype_jobapplication_corporate_philosophy_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='name',
            field=models.CharField(max_length=255, verbose_name='書類名'),
        ),
        migrations.AlterField(
            model_name='jobapplication',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='その他'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='experience',
            field=models.TextField(blank=True, help_text='これまでであなたが注力したことを具体的に記入してください。', verbose_name='職務経歴・学業経験・開発経験'),
        ),
        migrations.CreateModel(
            name='InterviewLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stage', models.CharField(help_text='例: 一次面接, 最終面接', max_length=100, verbose_name='選考段階')),
                ('interview_date', models.DateField(verbose_name='実施日')),
                ('questions_asked', models.TextField(blank=True, verbose_name='質問された内容')),
                ('self_evaluation', models.TextField(blank=True, verbose_name='自己評価・感想')),
                ('next_steps', models.TextField(blank=True, verbose_name='次のステップ・連絡事項')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job_application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interview_logs', to='jobinfo_application.jobapplication')),
            ],
            options={
                'ordering': ['-interview_date'],
            },
        ),
        migrations.CreateModel(
            name='EntrySheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(verbose_name='設問内容')),
                ('answer', models.TextField(blank=True, verbose_name='回答')),
                ('ai_draft', models.TextField(blank=True, verbose_name='AIによるドラフト')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job_application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entry_sheets', to='jobinfo_application.jobapplication')),
            ],
        ),
    ]
