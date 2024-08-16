from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from .forms import PostForm, CommentForm
from .models import Post, Category, Comment
from django.views.generic import (
    CreateView, DeleteView, DetailView, UpdateView, ListView
)
from django.db.models import Count
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.views import View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User


class OnlyAuthorMixin(UserPassesTestMixin):
    """Миксин для ограничения доступа"""

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class UserCanDeleteMixin(UserPassesTestMixin):
    """
    Миксин, позволяющий удалять объект только в том случае,
    если текущий пользователь является автором объекта
    """

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


def get_filter_posts(
        is_published=True,
        pub_date_lte=None,
        category_is_published=True):
    if pub_date_lte is None:
        pub_date_lte = timezone.now()
    return Post.objects.select_related(
        'author', 'category', 'location'
    ).filter(
        is_published=is_published,
        pub_date__lte=pub_date_lte,
        category__is_published=category_is_published,
    ).order_by('-pub_date')


class PostListView(ListView):
    """Класс отображения постов в блоге"""

    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = get_filter_posts()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        return queryset.annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PostDetailView(DetailView):
    """Представление для отображения детальной информации о посте"""

    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'id'

    def get(self, request, *args, **kwargs):
        post = self.get_object()

        is_post_unpublished = not post.is_published
        is_post_in_future = post.pub_date > timezone.now()
        is_category_unpublished = not post.category.is_published
        is_user_not_author = post.author != request.user

        if (
            (is_post_unpublished or is_post_in_future or
             is_category_unpublished)
            and is_user_not_author
        ):
            raise Http404("Пост не найден или доступен только автору.")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = Comment.objects.filter(
            post=self.object).order_by('created_at')
        context['comments'] = comments
        context['form'] = CommentForm()
        return context


class CategoryPostsView(View):
    """Класс категории постов"""

    template_name = 'blog/category.html'
    paginate_by = 10

    def get(self, request, category_slug):
        category = get_object_or_404(
            Category, slug=category_slug, is_published=True
        )
        posts = Post.objects.filter(
            category=category,
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
        paginator = Paginator(posts, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {'category': category, 'page_obj': page_obj}
        return render(request, self.template_name, context)


class PostCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания нового поста в блоге"""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class EditPostView(LoginRequiredMixin, UpdateView):
    """Класс редактирования поста"""

    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', id=post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'id': self.object.id})


class DeletePostView(LoginRequiredMixin, DeleteView):
    """Класс удаления поста"""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', id=post.id)
        return super().dispatch(request, *args, **kwargs)


class CommentPostView(UpdateView):
    """Класс для обновления определенного комментария к заданному посту"""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        post_id = self.kwargs['post_id']
        comment_id = self.kwargs['comment_id']
        comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

        if comment.author != self.request.user:
            raise PermissionDenied(
                "Вы не можете редактировать чужие комментарии."
            )

        return comment

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ProfileDetailView(ListView):
    """Представление для отображения профиля пользователя с его постами"""

    template_name = 'blog/profile.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user == self.user:
            return Post.objects.filter(
                author=self.user).annotate(
                    comment_count=Count('comments')).order_by('-pub_date')
        else:
            return Post.objects.filter(
                author=self.user, is_published=True).annotate(
                    comment_count=Count('comments')).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.user
        context['username'] = self.user.username

        full_name = self.user.get_full_name()
        if not full_name:
            context['profile'].first_name = self.user.username

        context['full_name'] = full_name
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для обновления профиля пользователя"""

    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'email']

    def dispatch(self, request, *args, **kwargs):
        user = self.get_object()
        if user != request.user:
            raise PermissionDenied("Вы не можете редактировать чужой профиль.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostDeleteView(LoginRequiredMixin, UserCanDeleteMixin, DeleteView):
    """Представление для удаления поста в блоге"""

    model = Post
    template_name = 'blog/delete.html'
    success_url = reverse_lazy('blog:index')

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания нового комментария к посту"""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'id': self.kwargs['post_id']})

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        context['post'] = post
        context['comments'] = self.get_comment_queryset(post)
        return context

    def get_comment_queryset(self, post):
        return Comment.objects.filter(post=post).order_by('-created')


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Представление для удаления комментария"""

    model = Comment
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'id': self.get_object().post_id}
        )

    def get_object(self):
        comment_id = self.kwargs['comment_id']
        post_id = self.kwargs['post_id']
        return get_object_or_404(Comment, id=comment_id, post_id=post_id)

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user
