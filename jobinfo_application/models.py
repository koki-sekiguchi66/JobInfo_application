from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    skills = models.TextField(
        blank=True, 
        verbose_name="スキル・資格",
        help_text="プログラミング言語、フレームワーク、保有資格など記入してください。"
    )
    experience = models.TextField(
        blank=True, 
        verbose_name="職務経歴・学業経験",
        help_text="これまでであなたが注力したことを具体的に記入してください。"
    )
    self_pr = models.TextField(
        blank=True,
        verbose_name="自己PR",
        help_text="あなたの強みや、仕事に対する価値観を記入してください。"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class JobType(models.Model):
    """職種モデル"""
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name
    
class JobApplication(models.Model):
    STATUS_CHOICES = [('検討中', '応募検討中'), ('応募済', '書類応募済'), ('選考中', '選考中'), ('内定', '内定'), ('見送り', '見送り')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, verbose_name="企業名")
    job_title = models.CharField(max_length=255, verbose_name="応募職種")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='検討中', verbose_name="選考ステージ")
    job_types = models.ManyToManyField(JobType, blank=True, verbose_name="職種カテゴリ")

    next_action = models.CharField(
                    max_length=255, 
                    blank=True, 
                    null=True, 
                    verbose_name="次のタスク",
                    help_text="例：面接,グループディスカッション、Webテスト受験など" 
                    )
    
    next_action_date = models.DateField(
                            blank=True, 
                            null=True, 
                            verbose_name="タスクの期日/予定日", 
                            help_text="面接の日付や、提出物の締切日などを入力します。" 
                            )

    corporate_philosophy = models.TextField(
                                blank=True, 
                                null=True, 
                                verbose_name="経営理念・ビジョン", 
                                help_text="企業の公式サイトに記載の経営理念・ビジョンをコピー＆ペーストしてください。"
                                )
    
    ideal_candidate = models.TextField(
                        blank=True, 
                        null=True, 
                        verbose_name="企業の求める人物像", 
                        help_text="企業の採用ページなどに記載の「求める人物像」をコピー＆ペーストしてください。"
                        )
    
    job_description = models.TextField(
                        blank=True, 
                        null=True, 
                        verbose_name="業務内容", 
                        help_text="企業の業務内容をコピー＆ペーストしてください。"
                        )
    

    notes = models.TextField(blank=True, null=True, verbose_name="備考")
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日")


    def __str__(self): 
        return f"{self.company_name} - {self.job_title}"
    
    def get_absolute_url(self): 
        return reverse('application-detail', kwargs={'pk': self.pk})
    

class Document(models.Model):
    job_application = models.ForeignKey(JobApplication, related_name='documents', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name="書類名（例：エントリーシート_v1など）")
    uploaded_file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): 
        return self.name