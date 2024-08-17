from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


MAX_TEXT_LENGTH = 30


class Published(models.Model):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        abstract = True


class Created(models.Model):
    created_at = models.DateTimeField('Добавлено', auto_now_add=True,)

    class Meta:
        abstract = True


class Category(Published, Created):

    title = models.CharField('Заголовок', max_length=settings.MAX_FIELD_LENGTH)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы, '
            'цифры, дефис и подчёркивание.'
        ),
        unique=True
    )

    class Meta:

        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:settings.REPRESENTATION_LENGTH]


class Location(Published, Created):

    name = models.CharField('Название места',
                            max_length=settings.MAX_FIELD_LENGTH)

    class Meta:

        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:settings.REPRESENTATION_LENGTH]


class Post(Published, Created):
    title = models.CharField('Заголовок', max_length=settings.MAX_FIELD_LENGTH)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text='Если установить дату и время в будущем — '
                  'можно делать отложенные публикации.'
    )
    image = models.ImageField(verbose_name='Картинка в публикации', blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )
    category = models.ForeignKey(
        Category, null=True,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
    )
    location = models.ForeignKey(
        Location,
        blank=True, null=True,
        on_delete=models.SET_NULL,
        verbose_name='Местоположение',
    )

    class Meta:
        default_related_name = 'posts'
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title[:settings.REPRESENTATION_LENGTH]

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=(self.pk,))


class Comment(Published, Created):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='comments',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Комментируемый пост',
        related_name='comments',
    )
    text = models.TextField(verbose_name='Текст комментария')

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return self.text[MAX_TEXT_LENGTH]
