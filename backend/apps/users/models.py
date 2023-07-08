from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, validate_email
from django.db import models
from django.utils.translation import gettext_lazy as _

from foodgram.settings import MAX_LENGTH_USERFIELDS, REGEX_USER


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='E-mail',
        max_length=254,
        unique=True,
        blank=False,
        error_messages={
            'unique': _('Пользователь с таким E-mail уже существует!'),
        },
        help_text=_('Укажите свой E-mail'),
        validators=[validate_email]
    )
    username = models.CharField(
        verbose_name=_('Уникальное имя пользователя'),
        max_length=MAX_LENGTH_USERFIELDS,
        unique=True,
        db_index=True,
        error_messages={
            'unique': _('Пользователь с таким юзернеймом уже существует!'),
        },
        help_text=_('Укажите свой юзернейм'),
        validators=[
            RegexValidator(
                REGEX_USER,
                message=_('Недопустимые символы в имени пользователя.')
            )
        ]
    )
    first_name = models.CharField(
        verbose_name=_('Имя'),
        max_length=MAX_LENGTH_USERFIELDS,
        help_text=_('Укажите своё имя')
    )
    last_name = models.CharField(
        verbose_name=_('Фамилия'),
        max_length=MAX_LENGTH_USERFIELDS,
        help_text=_('Укажите свою фамилию')
    )
    joined = models.DateTimeField(
        verbose_name=_('Дата регистрации'),
        auto_now_add=True
    )
    password = models.CharField(
        verbose_name=_('Пароль'),
        max_length=MAX_LENGTH_USERFIELDS,
        help_text=_('Введите пароль')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.get_full_name()


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name=_('Подписчик'),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('Автор'),
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique follow',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'
