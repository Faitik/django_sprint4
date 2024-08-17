from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class OnlyAuthorMixin(UserPassesTestMixin):
    """Миксин для ограничения доступа"""

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class UserCanDeleteMixin(UserPassesTestMixin):
    """
    Миксин, позволяющий удалять объект только в том случае,
    если текущий пользователь является автором объекта
    """

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class AuthorRequiredMixin(UserPassesTestMixin):
    """Миксин выполняющий проверку авторства"""

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', id=post.id)
        return super().dispatch(request, *args, **kwargs)
