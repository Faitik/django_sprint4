from django.conf import settings
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from .forms import PostForm, CommentForm
from .models import Post, Category, Comment, User
from django.views.generic import (
    CreateView, DeleteView, DetailView, UpdateView, ListView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.views import View


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


def get_filter_posts(is_published=True,
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
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'
    paginate_by = 10 

    def get_queryset(self):
        queryset = get_filter_posts()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        # Используем safe check для получения объекта
        post = get_object_or_404(Post, id=self.kwargs['id'])
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Предполагаем, что в модели Comment есть поле post (ForeignKey)
        comments = Comment.objects.filter(
            post=self.object).order_by('created_at')
        context['comments'] = comments
        context['form'] = CommentForm()
        return context


class CategoryPostsView(View):
    template_name = 'blog/category.html'

    def get(self, request, category_slug):
        category = get_object_or_404(
            Category, slug=category_slug, is_published=True
            )
        posts = Post.objects.filter(
            category=category, category__is_published=True
            )
        context = {'category': category, 'post_list': posts}
        return render(request, self.template_name, context)


class PostCreateView(CreateView):
    template_name = 'blog/create.html'

    def get(self, request, *args, **kwargs):
        form = PostForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = PostForm(request.POST, files=request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:index')
        return render(request, self.template_name, {'form': form})


class EditPostView(UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'


class DeletePostView(DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class CommentPostView(UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        post_id = self.kwargs['post_id']
        comment_id = self.kwargs['comment_id']
        return get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ProfileDetailView(DetailView):
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        # Получение объекта пользователя по username
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Фильтрация постов по автору
        context['page_obj'] = Post.objects.filter(author=self.object)
        return context


class ProfileUpdateView(UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = '__all__'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class UserCanDeleteMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostDeleteView(LoginRequiredMixin, UserCanDeleteMixin, DeleteView):
    model = Post
    template_name = 'blog/delete.html'
    success_url = reverse_lazy('blog:index')

    def test_func(self):
        post = self.get_object()
        return post.author == self.request.user


class CommentCreateView(LoginRequiredMixin, CreateView):
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
        # Здесь вы можете определять ваш queryset для комментариев
        return Comment.objects.filter(post=post).order_by('-created')


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Класс удаления комментария"""
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
