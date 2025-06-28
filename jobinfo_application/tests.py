from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime

from .models import JobApplication, Document
from .forms import JobApplicationForm


# モデルのテスト

class ApplicationModelTests(TestCase):
    """モデルの基本的な動作に関するテストをまとめたクラス"""

    def setUp(self):
        """このテストクラスで共通して使用するオブジェクトを作成する"""
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.application = JobApplication.objects.create(
            user=self.user,
            company_name='test company',
            job_title='test'
        )

    def test_job_application_str_representation(self):
        """JobApplicationモデルの__str__メソッドが、意図した通りの読みやすい文字列を返すかテストする"""
        self.assertEqual(str(self.application), 'test company - test')

    def test_document_str_representation(self):
        """Documentモデルの__str__メソッドが、意図した通りの読みやすい文字列を返すかテストする"""
        document = Document.objects.create(job_application=self.application, name='test.pdf')
        self.assertEqual(str(document), 'test.pdf')

    def test_job_application_auto_now_add(self):
        """JobApplication作成時に、applied_at（登録日）が自動的に設定されるかテストする"""
        self.assertIsNotNone(self.application.applied_at)
        self.assertIsInstance(self.application.applied_at, datetime.datetime)


# フォームのテスト

class ApplicationFormTests(TestCase):
    """フォームのバリデーション（入力値チェック）に関するテストをまとめたクラス"""

    def test_job_application_form_valid(self):
        """JobApplicationFormに有効なデータを渡した際に、フォームが有効（valid）と判断されるかテストする"""
        form_data = {'company_name': 'Valid Company', 'job_title': 'Valid Job', 'status': '検討中'}
        form = JobApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_job_application_form_invalid_with_missing_data(self):
        """JobApplicationFormで必須フィールドが空の場合に、フォームが無効（invalid）と判断されるかテストする"""
        form_data = {'company_name': '', 'job_title': 'Invalid Job', 'status': '検討中'}
        form = JobApplicationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)


# ビューのテスト

class ApplicationViewTests(TestCase):
    """各ページの表示や操作（ビュー）に関するテストをまとめたクラス"""

    def setUp(self):
        """このテストクラスで共通して使用するオブジェクト（ユーザー、応募情報など）を作成する"""
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        self.app1_of_user1 = JobApplication.objects.create(user=self.user1, company_name='companyA', job_title='testA')
        self.app2_of_user2 = JobApplication.objects.create(user=self.user2, company_name='companyB', job_title='testB')

    # 認証・認可に関するテスト 
    def test_unauthenticated_user_is_redirected_to_login(self):
        """未ログインユーザーは、ログイン必須ページにアクセスするとログインページへリダイレクトされる"""
        response = self.client.get(reverse('application-list'))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_user_can_only_see_their_own_applications_in_list(self):
        """応募一覧ページに、自分自身の応募情報だけが表示される（他人の情報は表示されない）"""
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('application-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'companyA')
        self.assertNotContains(response, 'companyB')

    def test_user_cannot_access_others_detail_page(self):
        """ユーザーは、他人の応募情報の詳細ページにアクセスできない（404エラーとなる）"""
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('application-detail', kwargs={'pk': self.app2_of_user2.pk}))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_update_others_application(self):
        """ユーザーは、他人の応募情報を更新しようとしてもできない（404エラーとなる）"""
        self.client.login(username='user1', password='password1')
        response = self.client.post(reverse('application-update', kwargs={'pk': self.app2_of_user2.pk}), {'company_name': '不正な更新', 'job_title': 'Hacker', 'status': '検討中'})
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_others_application(self):
        """ユーザーは、他人の応募情報を削除しようとしてもできない（404エラーとなる）"""
        self.client.login(username='user1', password='password1')
        response = self.client.post(reverse('application-delete', kwargs={'pk': self.app2_of_user2.pk}))
        self.assertEqual(response.status_code, 404)

    # CRUD機能に関するテスト 
    def test_list_view_displays_message_for_no_applications(self):
        """応募情報が一件もない場合に、「まだ応募情報がありません」というメッセージが表示される"""
        new_user = User.objects.create_user(username='newuser', password='password3')
        self.client.login(username='newuser', password='password3')
        response = self.client.get(reverse('application-list'))
        self.assertContains(response, 'まだ応募情報がありません')

    def test_successful_application_creation(self):
        """有効なデータで、応募情報の新規作成が正しく行える"""
        self.client.login(username='user1', password='password1')
        count_before = JobApplication.objects.filter(user=self.user1).count()
        self.client.post(reverse('application-create'), {'company_name': 'companyC', 'job_title': 'testC', 'status': '検討中'})
        count_after = JobApplication.objects.filter(user=self.user1).count()
        self.assertEqual(count_after, count_before + 1)

    def test_failed_application_creation_rerenders_form(self):
        """無効なデータ（必須項目が空）で新規作成しようとすると、エラー付きでフォームが再表示される"""
        self.client.login(username='user1', password='password1')
        response = self.client.post(reverse('application-create'), {'company_name': '', 'job_title': 'test', 'status': '検討中'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('company_name', response.context['form'].errors)

    def test_successful_application_update(self):
        """応募情報の更新が正しく行われ、データベースに反映される"""
        self.client.login(username='user1', password='password1')
        self.client.post(reverse('application-update', kwargs={'pk': self.app1_of_user1.pk}), {'company_name': 'new company', 'job_title': 'new job', 'status': '選考中'})
        self.app1_of_user1.refresh_from_db()
        self.assertEqual(self.app1_of_user1.company_name, 'new company')
        self.assertEqual(self.app1_of_user1.status, '選考中')

    def test_successful_application_deletion(self):
        """応募情報の削除が正しく行われ、データベースから消える"""
        self.client.login(username='user1', password='password1')
        count_before = JobApplication.objects.count()
        self.client.post(reverse('application-delete', kwargs={'pk': self.app1_of_user1.pk}))
        count_after = JobApplication.objects.count()
        self.assertEqual(count_after, count_before - 1)
        self.assertFalse(JobApplication.objects.filter(pk=self.app1_of_user1.pk).exists())

    # 書類アップロードとAI機能のテスト 
    def test_successful_document_upload(self):
        """書類が正しくアップロードされ、該当の応募情報に紐づく"""
        self.client.login(username='user1', password='password1')
        dummy_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        self.client.post(reverse('add-document', kwargs={'pk': self.app1_of_user1.pk}), {'name': 'test doc', 'uploaded_file': dummy_file})
        self.assertEqual(self.app1_of_user1.documents.count(), 1)
        self.assertEqual(self.app1_of_user1.documents.first().name, 'test doc')

    @patch('jobinfo_application.views.openai.chat.completions.create')
    def test_ai_draft_generation_with_successful_mock_api(self, mock_openai_create):
        """（モックを使って）AIのAPI呼び出しが成功した場合、生成されたテキストが画面に表示される"""
        self.client.login(username='user1', password='password1')
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "AIによるドラフト成功"
        mock_openai_create.return_value = mock_response
        self.app1_of_user1.job_description = "求人情報あり"
        self.app1_of_user1.save()
        response = self.client.post(reverse('generate-draft', kwargs={'pk': self.app1_of_user1.pk}), {'user_skills': 'Python'})
        mock_openai_create.assert_called_once()
        self.assertContains(response, "AIによるドラフト成功")

    @patch('jobinfo_application.views.openai.chat.completions.create')
    def test_ai_draft_generation_with_failed_mock_api(self, mock_openai_create):
        """（モックを使って）AIのAPI呼び出しが失敗（例外発生）した場合、エラーメッセージが表示される"""
        self.client.login(username='user1', password='password1')
        mock_openai_create.side_effect = Exception("API connection error")
        self.app1_of_user1.job_description = "求人情報あり"
        self.app1_of_user1.save()
        response = self.client.post(reverse('generate-draft', kwargs={'pk': self.app1_of_user1.pk}), {'user_skills': 'Python'})
        self.assertContains(response, "エラー:")