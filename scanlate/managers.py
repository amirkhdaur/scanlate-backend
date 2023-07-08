from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class UserManager(BaseUserManager):
    def create_user(self, username, email, name, password, discord_user_id):
        if not username:
            raise ValueError('Username must be set')
        if not email:
            raise ValueError('Email must be set')
        if not name:
            raise ValueError('Name must be set')

        username = AbstractBaseUser.normalize_username(username)
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, name=name, discord_user_id=discord_user_id)
        user.set_password(password)
        user.save()

        return user
