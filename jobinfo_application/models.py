from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    skills = models.TextField(
        blank=True, 
        verbose_name="スキル・資格",
        help_text="プログラミング言語、フレームワーク、保有資格などを自由にご記入ください。"
    )
    experience = models.TextField(
        blank=True, 
        verbose_name="職務経歴・学業経験",
        help_text="これまでであなたが注力したことなどを具体的に記述してください。"
    )
    self_pr = models.TextField(
        blank=True,
        verbose_name="自己PR",
        help_text="あなたの強みや、仕事に対する価値観などを自由にご記入ください。"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class JobApplication(models.Model):
    STATUS_CHOICES = [('検討中', '応募検討中'), ('応募済', '書類応募済'), ('選考中', '選考中'), ('内定', '内定'), ('見送り', '見送り')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, verbose_name="企業名")
    job_title = models.CharField(max_length=255, verbose_name="応募職種")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='検討中', verbose_name="選考ステージ")

    next_action = models.CharField(
    max_length=255, 
    blank=True, 
    null=True, 
    verbose_name="次のタスク",
    help_text="例：面接日程の調整メール返信, Webテスト受験など" 
)
    
    next_action_date = models.DateField(
    blank=True, 
    null=True, 
    verbose_name="タスクの期日/予定日", 
    help_text="面接の日付や、タスクの締切日などを入力します。" 
)

    job_description = models.TextField(
    blank=True, 
    null=True, 
    verbose_name="求人情報",  
    help_text="ここに求人情報をコピー＆ペーストすると、AIによる志望動機作成支援機能が利用できます。"
    )

    notes = models.TextField(blank=True, null=True, verbose_name="備考")
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日")


    def __str__(self): 
        return f"{self.company_name} - {self.job_title}"
    
    def get_absolute_url(self): 
        return reverse('application-detail', kwargs={'pk': self.pk})
    

class Document(models.Model):
    job_application = models.ForeignKey(JobApplication, related_name='documents', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name="書類名（例：職務経歴書_v2）")
    uploaded_file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): 
        return self.name