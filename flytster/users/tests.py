from datetime import timedelta
from uuid import uuid4

from django.core.urlresolvers import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import FlytsterUser
from authentication.models import AuthToken, EmailToken, PasswordToken, PhoneToken


class TestUserMixin(object):

    def setUp(self):
        user = FlytsterUser.objects.create_user(
            first_name='Fly',
            last_name='High',
            email='flyhigh@gmail.com',
            password='Password1'
        )

        assert(user)
        user.verify_email_token(user.email_token.token)

        self.user = user
        self.auth = {'HTTP_AUTHORIZATION': user.auth_tokens.latest('timestamp').token}


class FlytsterSuperUserTest(APITestCase):
    def test_create_super_user(self):
        user = FlytsterUser.objects.create_superuser(
            first_name='Boss',
            last_name='Man',
            email='bossman@gmail.com',
            password='Password1'
        )

        self.assertTrue(user)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.get_full_name(), 'Boss Man')
        self.assertEqual(user.__str__(), 'bossman@gmail.com')


class BadAuthAPITest(TestUserMixin, APITestCase):

    def test_expired_auth(self):
        token = self.user.auth_tokens.latest('timestamp')
        token.timestamp = timezone.now() - timedelta(days=14)
        token.save()

        url = reverse('get_update_user')

        response = self.client.get(url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_auth(self):
        url = url = reverse('get_update_user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RegistrationTest(APITestCase):

    def test_register_user(self):
        url = reverse('register')
        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'dabbin@gmail.com',
            'password': 'Password1'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['token'])
        self.assertEqual(response.data['email'], data['email'])

    def test_register_user_uppercase_email(self):
        url = reverse('register')
        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'DABBIN@gmail.com',
            'password': 'Password1'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['token'])
        self.assertEqual(response.data['email'], 'dabbin@gmail.com')

    def test_register_bad_email(self):
        url = reverse('register')
        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'DABBIN',
            'password': 'Password1'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_no_name(self):
        url = reverse('register')
        data = {
            'email': 'dabbin@gmail.com',
            'password': 'Password1'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_dup_email(self):
        url = reverse('register')
        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'dabbin@gmail.com',
            'password': 'Password1'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'dabbin@gmail.com',
            'password': 'Password1'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_register_no_pass(self):
        url = reverse('register')
        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'dabbin@gmail.com'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_bad_pass(self):
        url = reverse('register')
        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'dabbin@gmail.com',
            'password': 'Password'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            'first_name': 'Cam',
            'last_name': 'Newton',
            'email': 'dabbin@gmail.com',
            'password': 'Pass1'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(TestUserMixin, APITestCase):

    def test_login(self):
        url = reverse('login')
        old_token = self.auth['HTTP_AUTHORIZATION']
        data = {
            'email': 'flyhigh@gmail.com',
            'password': 'Password1',
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Fly')
        self.assertEqual(response.data['last_name'], 'High')
        self.assertEqual(response.data['id'], self.user.id)
        self.assertNotEqual(response.data['token'], old_token)

    def test_login_user_uppercase_email(self):
        url = reverse('login')
        old_token = self.auth['HTTP_AUTHORIZATION']
        data = {
            'email': 'Flyhigh@gmail.com',
            'password': 'Password1',
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Fly')
        self.assertEqual(response.data['last_name'], 'High')
        self.assertEqual(response.data['id'], self.user.id)
        self.assertNotEqual(response.data['token'], old_token)

    def test_login_no_old_token(self):
        url = reverse('login')
        old_token = AuthToken.objects.get(user=self.user)
        old_token.delete()
        data = {
            'email': 'Flyhigh@gmail.com',
            'password': 'Password1',
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Fly')
        self.assertEqual(response.data['last_name'], 'High')
        self.assertEqual(response.data['id'], self.user.id)
        self.assertIn('token', response.data)

    def test_login_no_user_email_exists(self):
        url = reverse('login')
        data = {
            'email': 'high@gmail.com',
            'password': 'Password1',
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_invalid_email(self):
        url = reverse('login')
        data = {
            'email': 'Flyhigh.com',
            'password': 'Password1',
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_login_incorrect_pass(self):
        url = reverse('login')

        data = {
            'email': 'Flyhigh@gmail.com',
            'password': 'password1',
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LogoutTest(TestUserMixin, APITestCase):

    def test_logout(self):
        url = reverse('login')
        data = {
            'email': 'flyhigh@gmail.com',
            'password': 'Password1',
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'])
        self.assertEqual(response.data['id'], self.user.id)

        auth = {'HTTP_AUTHORIZATION': response.data['token']}

        url = reverse('logout')

        response = self.client.delete(url, **auth)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_double_logout(self):
        url = reverse('logout')

        response = self.client.delete(url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.delete(url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GetUpdateUserTest(TestUserMixin, APITestCase):

    def test_get_user(self):
        url = reverse('get_update_user')

        response = self.client.get(url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_user(self):
        url = reverse('get_update_user')
        data = {'first_name': 'Boomer'}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['first_name'], 'Boomer')

    def test_update_user_email(self):
        url = reverse('get_update_user')
        data = {'email': 'booyah@gmail.com'}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['email_pending'], data['email'])

        user = FlytsterUser.objects.get(id=self.user.id)
        user.verify_email_token(user.email_token.token)

        response = self.client.get(url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['email'], data['email'])
        self.assertFalse(response.data['email_pending'])
        self.assertTrue(response.data['email_verified'])

    def test_update_user_phone(self):
        new_phone = '3174554303'
        url = reverse('get_update_user')
        data = {'phone': new_phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['phone_pending'], new_phone)
        self.assertEqual(response.data['phone'], None)

    def test_update_user_phone_then_verify(self):
        new_phone = '3174554303'
        url = reverse('get_update_user')
        data = {'phone': new_phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['phone_pending'], new_phone)
        self.assertEqual(response.data['phone'], None)

        token = PhoneToken.objects.get(user=self.user).token
        url = reverse('verify_phone')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertTrue(response.data['phone_verified'])
        self.assertEqual(response.data['phone'], new_phone)

        url = reverse('get_update_user')
        data = {'phone': None}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['phone_pending'], None)
        self.assertEqual(response.data['phone'], None)

    def test_update_user_phone_new_phone(self):
        self.user.phone = '3174554303'
        self.user.phone_verified = True
        self.user.save()

        user_id = self.user.id
        new_phone = '3174554304'

        url = reverse('get_update_user')
        data = {'phone': new_phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], user_id)
        self.assertEqual(response.data['phone_pending'], new_phone)
        self.assertEqual(response.data['phone'], self.user.phone)

    def test_update_user_phone_new_phone_old_phone(self):
        self.user.phone = '3174554303'
        self.user.phone_verified = True
        self.user.save()

        user_id = self.user.id
        new_phone = '3174554304'

        url = reverse('get_update_user')
        data = {'phone': new_phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], user_id)
        self.assertEqual(response.data['phone_pending'], new_phone)
        self.assertEqual(response.data['phone'], self.user.phone)

        data = {'phone': self.user.phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], user_id)
        self.assertEqual(response.data['phone_pending'], None)
        self.assertEqual(response.data['phone'], self.user.phone)

    def test_update_user_phone_token_changes(self):
        self.user.phone = '3174554303'
        self.user.phone_verified = True
        self.user.save()

        user_id = self.user.id
        new_phone = '3174554304'

        url = reverse('get_update_user')
        data = {'phone': new_phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], user_id)
        self.assertEqual(response.data['phone_pending'], new_phone)
        self.assertEqual(response.data['phone'], self.user.phone)

        token = PhoneToken.objects.get(user=self.user).token

        new_phone = '3174554305'
        url = reverse('get_update_user')
        data = {'phone': new_phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], user_id)
        self.assertEqual(response.data['phone_pending'], new_phone)
        self.assertEqual(response.data['phone'], self.user.phone)

        new_token = PhoneToken.objects.get(user=self.user).token

        self.assertNotEqual(token, new_token)

    def test_update_user_phone_bad_data(self):
        new_phone = '10notvalid'

        url = reverse('get_update_user')

        data = {'phone': new_phone}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data)
        self.assertEqual(response.data['phone'][0], 'Phone numbers must be 10 digits.')

    def test_update_user_phone_and_email(self):
        self.user.phone = '3174554303'
        self.user.phone_verified = True
        self.user.save()

        user_id = self.user.id
        new_phone = '3174554304'
        new_email = 'flyhigh2222@gmail.com'

        url = reverse('get_update_user')
        data = {'phone': new_phone, 'email': new_email}

        response = self.client.patch(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data['id'], user_id)
        self.assertEqual(response.data['email_pending'], new_email)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['phone_pending'], new_phone)
        self.assertEqual(response.data['phone'], self.user.phone)


class VerifyEmailTest(TestUserMixin, APITestCase):

    def test_verify_email(self):
        self.user.send_verification_email('flyhigh2@gmail.com')
        token = EmailToken.objects.get(user=self.user).token
        url = reverse('verify_email')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'flyhigh2@gmail.com')
        self.assertTrue(response.data['email_verified'])
        self.assertFalse(response.data['email_pending'])


    def test_verify_email_bad_token(self):
        self.user.send_verification_email('flyhigh@gmail.com')
        token = '$$$$$$$$$$'
        url = reverse('verify_email')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_wrong_token(self):
        self.user.send_verification_email('flyhigh2@gmail.com')
        good_token = EmailToken.objects.get(user=self.user).token
        bad_token = uuid4().hex[:20]
        while good_token == bad_token:
            bad_token = uuid4().hex[:20]
        url = reverse('verify_email')

        data = {'token': bad_token}
        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['detail'])
        self.assertIn('invalid', response.data['detail'].lower())

    def test_verify_email_expired_code(self):
        self.user.send_verification_email('flyhigh2@gmail.com')
        et = EmailToken.objects.get(user=self.user)
        et.timestamp = timezone.now() - timedelta(days=7)
        et.save()
        token = et.token
        url = reverse('verify_email')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['detail'])
        self.assertIn('expired', response.data['detail'].lower())

    def test_verify_email_no_code(self):
        self.assertFalse(EmailToken.objects.filter(user=self.user).exists())
        token = uuid4().hex[:20]
        url = reverse('verify_email')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['detail'])
        self.assertIn('invalid', response.data['detail'].lower())


class VerifyPhoneTest(TestUserMixin, APITestCase):

    def test_verify_phone(self):
        self.user.send_verification_sms('3174554303')
        token = PhoneToken.objects.get(user=self.user).token

        url = reverse('verify_phone')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertTrue(response.data['phone_verified'])
        self.assertEqual(response.data['phone'], '3174554303')

    def test_verify_phone_bad_token(self):
        self.user.send_verification_sms('3174554303')
        token = '$$$$$$$$$'

        url = reverse('verify_phone')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_phone_wrong_token(self):
        self.user.send_verification_sms('3174554303')
        token = PhoneToken.objects.get(user=self.user).token
        bad_token = uuid4().hex[:6]
        while token == bad_token:
            bad_token = uuid4().hex[:6]

        url = reverse('verify_phone')
        data = {'token': bad_token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['detail'])
        self.assertIn('invalid', response.data['detail'].lower())

    def test_verify_phone_expired_token(self):
        self.user.send_verification_sms('3174554303')
        pt = PhoneToken.objects.get(user=self.user)
        pt.timestamp = timezone.now() - timedelta(days=7)
        pt.save()
        token = pt.token

        url = reverse('verify_phone')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['detail'])
        self.assertIn('expired', response.data['detail'].lower())

    def test_verify_phone_no_token(self):
        url = reverse('verify_phone')
        data = {'token': 'abc123'}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['detail'])
        self.assertIn('does not have', response.data['detail'].lower())

    def test_verify_phone_existing_phone_exists(self):
        self.user.send_verification_sms('3174554303')
        token = PhoneToken.objects.get(user=self.user).token

        new_user = FlytsterUser.objects.create_user(
            first_name='Flytster',
            last_name='LLC',
            email='flytster@gmail.com',
            password='supersecret1',
            phone='3174554303'
        )

        url = reverse('verify_phone')
        data = {'token': token}

        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class ChangePasswordTest(TestUserMixin, APITestCase):

    def test_change_password(self):
        url = reverse('change_pass')
        data = {
            'old_password': 'Password1',
            'new_password': 'NewPass2',
        }
        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # refresh user from db
        user = FlytsterUser.objects.get(id=self.user.id)
        self.assertTrue(user.check_password(data['new_password']))

    def test_change_password_bad_password(self):
        url = reverse('change_pass')

        data = {
            'old_password': 'Password1',
            'new_password': 'basspassss',
        }
        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_wrong_old_pass(self):
        url = reverse('change_pass')

        data = {
            'old_password': 'NotTheRightPassword1',
            'new_password': 'NewPassword2',
        }
        response = self.client.post(url, data=data, format='json', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_no_auth(self):
        url = reverse('change_pass')

        data = {
            'old_password': 'Password1',
            'new_password': 'NewPassword2',
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RequestPassResetTest(TestUserMixin, APITestCase):

    def test_request_password_reset(self):
        url = reverse('request_pass')
        data = {'email': 'flyhigh@gmail.com'}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email', response.data['detail'])

    def test_request_password_reset_bad_input(self):
        url = reverse('request_pass')
        data = {'email': 'flyhigh'}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_password_reset_non_user(self):
        url = reverse('request_pass')
        data = {'email': 'nonuser@gmail.com'}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ResetPasswordTest(TestUserMixin, APITestCase):

    def test_reset_password(self):
        url = reverse('request_pass')
        data = {'email': self.user.email}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = PasswordToken.objects.get(user=self.user).token
        old_pass = self.user.password
        url = reverse('reset_pass')
        data = {
            'token': token,
            'new_password': 'NewPassword2'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'])
        new_pass = FlytsterUser.objects.get(email=self.user.email).password
        self.assertNotEqual(old_pass, new_pass)

    def test_reset_password_double(self):
        url = reverse('request_pass')
        data = {'email': self.user.email}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        first_token = PasswordToken.objects.get(user=self.user).token

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        second_token = PasswordToken.objects.get(user=self.user).token
        self.assertNotEqual(first_token, second_token)

    def test_reset_pass_bad_code(self):
        url = reverse('request_pass')
        data = {'email': self.user.email}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('reset_pass')
        data = {
            'reset_code': '$$$$$$$$$$$$',
            'new_password': 'NewPassword2'
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_pass_wrong_code(self):
        url = reverse('request_pass')
        data = {'email': self.user.email}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        good_token = PasswordToken.objects.get(user=self.user).token
        bad_token = uuid4().hex[:20]
        while good_token == bad_token:
            bad_token = uuid4().hex[:20]

        self.assertNotEqual(good_token, bad_token)

        url = reverse('reset_pass')
        data = {
            'token': bad_token,
            'new_password': 'NewPassword2'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_pass_expired_code(self):
        url = reverse('request_pass')
        data = {'email': self.user.email}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pt = PasswordToken.objects.get(user=self.user)
        pt.timestamp = timezone.now() - timedelta(days=7)
        pt.save()
        url = reverse('reset_pass')
        data = {
            'token': pt.token,
            'new_password': 'NewPassword2'
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_pass_bad_pass(self):
        url = reverse('request_pass')
        data = {'email': self.user.email}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = PasswordToken.objects.get(user=self.user).token
        url = reverse('reset_pass')
        data = {
            'token': token,
            'new_password': 'BadNewPass'
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_email_case_insensitivity(self):
        url = reverse('request_pass')
        data = {'email': 'FLYHIGH@GMAIL.com'}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = PasswordToken.objects.get(user=self.user).token
        old_pass = self.user.password
        url = reverse('reset_pass')
        data = {
            'token': token,
            'new_password': 'NewPassword2'
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['token'])
        new_pass = FlytsterUser.objects.get(email=self.user.email).password
        self.assertNotEqual(old_pass, new_pass)
