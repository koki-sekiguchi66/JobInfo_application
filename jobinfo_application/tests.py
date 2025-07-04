from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime

from .models import JobApplication, Document, UserProfile
from .forms import JobApplicationForm, UserProfileForm
from django.core import mail


class ModelAndSignalTests(TestCase):
    """モデルの基本動作と、ユーザー作成時のシグナルの動作"""

    def setUp(self):
        """ユーザー"""
        self.user = User.objects.create_user(username='user', password='password1')
        self.application = JobApplication.objects.create(
            user=self.user,
            company_name='test',
            job_title='エンジニア'
        )

    def test_user_profile_is_created_on_user_creation(self):
        """User作成時に、シグナルによってUserProfileが自動的に作成"""
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertEqual(self.user.profile.user.username, 'user')

    def test_job_application_str_representation(self):
        """JobApplicationモデルの__str__メソッドが、正しい文字列を返す"""
        self.assertEqual(str(self.application), 'test - エンジニア')

    def test_document_str_representation(self):
        """Documentモデルの__str__メソッドが、正しい文字列を返す"""
        document = Document.objects.create(job_application=self.application, name='test.pdf')
        self.assertEqual(str(document), 'test.pdf')


class FormTests(TestCase):
    """各フォームのバリデーション"""

    def test_job_application_form_is_valid(self):
        """JobApplicationFormに有効なデータを渡した際に、フォームが有効"""
        form_data = {'company_name': 'Valid Company', 'job_title': 'Valid Job', 'status': '検討中'}
        form = JobApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_job_application_form_is_invalid_with_missing_data(self):
        """JobApplicationFormで必須フィールドが空の場合に、フォームが無効"""
        form_data = {'company_name': '', 'job_title': 'Invalid Job', 'status': '検討中'}
        form = JobApplicationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)

    def test_user_profile_form_is_valid(self):
        """UserProfileFormに有効なデータを渡した際に、フォームが有効"""
        form_data = {'skills': 'Python', 'experience': 'None', 'self_pr': 'OK'}
        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())


class ViewTests(TestCase):
    """各ページの表示や操作"""

    def setUp(self):
        """ユーザー"""
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        
        self.user1.profile.skills = "Python, Django"
        self.user1.profile.save()

        self.app1_of_user1 = JobApplication.objects.create(user=self.user1, company_name='A', job_title='エンジニア')
        self.app2_of_user2 = JobApplication.objects.create(user=self.user2, company_name='B', job_title='デザイナー')

    # 認証・認可 
    def test_unauthenticated_user_cannot_access_list_view(self):
        """未ログインユーザーは、一覧ページにアクセス不可"""
        response = self.client.get(reverse('application-list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('application-list')}")

    def test_unauthenticated_user_cannot_create_application(self):
        """未ログインユーザーは、新規作成不可"""
        count_before = JobApplication.objects.count()
        response = self.client.post(reverse('application-create'), {
            'company_name': '不正な企業',
            'job_title': '不正な職種',
            'status': '検討中'
        })
        count_after = JobApplication.objects.count()
        self.assertEqual(count_before, count_after)        
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('application-create')}")

    def test_unauthenticated_user_cannot_update_application(self):
        """未ログインユーザーは、更新不可"""
        response = self.client.post(reverse('application-update', kwargs={'pk': self.app1_of_user1.pk}), {
            'company_name': '不正な更新'
        })
        self.app1_of_user1.refresh_from_db()
    
        self.assertEqual(self.app1_of_user1.company_name, 'A')
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('application-update', kwargs={'pk': self.app1_of_user1.pk})}")

    def test_login_required_for_profile_edit(self):
        """未ログインユーザーは、プロフィール編集ページにアクセス不可"""
        response = self.client.get(reverse('profile-edit'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile-edit')}")

    def test_unauthenticated_user_redirected(self):
        """未ログインユーザーは、ログインページへリダイレクト"""
        response = self.client.get(reverse('application-list'))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_user_can_only_see_own_applications(self):
        """一覧ページに、自分自身の応募情報だけが表示"""
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('application-list'))
        self.assertContains(response, 'A')
        self.assertNotContains(response, 'B')

    def test_user_cannot_access_others_detail_page(self):
        """ユーザーは、他人の応募情報の詳細ページにアクセス不可"""
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('application-detail', kwargs={'pk': self.app2_of_user2.pk}))
        self.assertEqual(response.status_code, 404)
    
    def test_user_cannot_update_others_application(self):
        """ユーザーは、他人の応募情報を更新不可"""
        self.client.login(username='user1', password='password1')
        response = self.client.post(reverse('application-update', kwargs={'pk': self.app2_of_user2.pk}), {
            'company_name': '不正な更新'
        })
        self.assertEqual(response.status_code, 404)

    def test_profile_edit_view_get(self):
        """ログイン時、自身のプロフィール編集ページを表示"""
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('profile-edit'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python, Django")

    def test_profile_edit_view_post_update(self):
        """プロフィール編集ページで、情報を正しく更新"""
        self.client.login(username='user1', password='password1')
        self.client.post(reverse('profile-edit'), {'skills': "React"})
        self.user1.profile.refresh_from_db()
        self.assertEqual(self.user1.profile.skills, "React")

    def test_list_view_empty_message(self):
        """応募情報がない場合に、エラー表示"""
        new_user = User.objects.create_user(username='newuser', password='password3')
        self.client.login(username='newuser', password='password3')
        response = self.client.get(reverse('application-list'))
        self.assertContains(response, 'まだ応募情報がありません')

    def test_application_creation(self):
        """応募情報の新規作成"""
        self.client.login(username='user1', password='password1')
        count_before = JobApplication.objects.filter(user=self.user1).count()
        response = self.client.post(reverse('application-create'), {'company_name': 'C', 'job_title': 'New', 'status': '検討中'})
        count_after = JobApplication.objects.filter(user=self.user1).count()
        self.assertEqual(count_after, count_before + 1)
        self.assertRedirects(response, reverse('application-detail', kwargs={'pk': JobApplication.objects.latest('id').pk}))

    def test_application_update(self):
        """応募情報の更新"""
        self.client.login(username='user1', password='password1')
        self.client.post(reverse('application-update', kwargs={'pk': self.app1_of_user1.pk}), {'company_name': 'D', 'job_title': 'エンジニア', 'status': '選考中'})
        self.app1_of_user1.refresh_from_db()
        self.assertEqual(self.app1_of_user1.company_name, 'D')

    def test_application_deletion(self):
        """応募情報の削除"""
        self.client.login(username='user1', password='password1')
        count_before = JobApplication.objects.count()
        self.client.post(reverse('application-delete', kwargs={'pk': self.app1_of_user1.pk}))
        count_after = JobApplication.objects.count()
        self.assertEqual(count_after, count_before - 1)


    def test_document_upload(self):
        """書類のアップロード"""
        self.client.login(username='user1', password='password1')
        dummy_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        self.client.post(reverse('add-document', kwargs={'pk': self.app1_of_user1.pk}), {'name': 'test doc', 'uploaded_file': dummy_file})
        self.assertEqual(self.app1_of_user1.documents.count(), 1)

    @patch('jobinfo_application.views.openai.chat.completions.create')
    def test_ai_draft_uses_profile_info(self, mock_openai_create):
        """AIドラフト生成時に、保存されたプロフィール情報がプロンプトに含まれている"""
        self.client.login(username='user1', password='password1')
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "AIドラフト"
        mock_openai_create.return_value = mock_response
        self.app1_of_user1.job_description = "求人情報"
        self.app1_of_user1.save()
        
        self.client.post(reverse('generate-draft', kwargs={'pk': self.app1_of_user1.pk}))
        
        mock_openai_create.assert_called_once()
        actual_prompt = mock_openai_create.call_args[1]['messages'][0]['content']
        self.assertIn("Python, Django", actual_prompt) 



class AuthenticationFlowsTests(TestCase):
    """サインアップ、パスワード変更、パスワードリセットなど一連の認証フローをテストする"""

    def setUp(self):
        """ユーザー"""
        self.user = User.objects.create_user(
            username='user',
            password='password1',
            email='test@example.com'
        )
        self.password_change_url = reverse('password_change')
        self.password_reset_url = reverse('password_reset')

    def test_password_change_view_loads_for_logged_in_user(self):
        """パスワード変更ページを表示"""
        self.client.login(username='user', password='password1')
        response = self.client.get(self.password_change_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change_form.html')

    def test_successful_password_change(self):
        """パスワードを変更したら、古いパスワードではログイン不可"""
        self.client.login(username='user', password='password1')
        new_password = 'new_strong_password1'
        response = self.client.post(self.password_change_url, {
            'old_password': 'password1',
            'new_password1': new_password,
            'new_password2': new_password,
        })
        self.assertRedirects(response, reverse('password_change_done'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password('password1'))

    def test_password_change_fails_with_wrong_old_password(self):
        """パスワードが間違っている場合、パスワード変更不可"""
        self.client.login(username='user', password='password1')
        response = self.client.post(self.password_change_url, {
            'old_password': 'password3',
            'new_password1': 'password2',
            'new_password2': 'password2',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '元のパスワードが間違っています。もう一度入力してください。')
    
    def test_password_reset_view_loads(self):
        """パスワードリセットページを表示"""
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')

    def test_password_reset_sends_email_for_valid_user(self):
        """有効なメールアドレスでリセット用のメールを送信"""
        self.client.post(self.password_reset_url, {'email': 'test@example.com'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'testserver のパスワードリセット')
        self.assertIn('user', mail.outbox[0].body)