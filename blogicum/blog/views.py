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


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


def get_filter_posts(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True):

    return Post.objects.select_related(
        'author', 'category', 'location',
    ).filter(
        is_published=is_published,
        pub_date__lte=pub_date__lte,
        category__is_published=category__is_published,
    )


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'  # Назовем контекст posts вместо page_obj
    paginate_by = 3

    def get_queryset(self):
        queryset = get_filter_posts()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        return queryset


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, id=self.kwargs['id'])
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = Comment.objects.filter(
            post_id=self.object).order_by('created_at')
        context['comments'] = comments
        context['form'] = CommentForm()
        return context


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    posts = get_filter_posts(
        category__is_published=True).filter(category=category)
    context = {'category': category, 'post_list': posts}

    return render(request, 'blog/category.html', context)


def post_create(request):
    template_name = 'blog/create.html'
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:index')
    return render(request, template_name, {'form': form})


class EditPostViews(UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'
    

class DeletePostView(DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class CommetPostView(CreateView):
    model = Comment  #Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class ProfileDetailView(DetailView):
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_obj'] = Post.objects.filter(author=self.object)
        return context


class CommentCreateView(CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'id': self.kwargs['post_id']})

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = Post.objects.get(id=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = Post.objects.get(id=self.kwargs['post_id'])
        context['comments'] = Comment.objects.filter(
            post_id=self.kwargs['post_id']
        )
        return context

    def test_func(self):
        return self.request.user.is_authenticated


class ProfileUpdateView(UpdateView):
    model = User  # Post
    template_name = 'blog/user.html'
    fields = '__all__'

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

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
    template_name = 'blog/delete.html'  # Используем существующий шаблон
    success_url = reverse_lazy('blog:index')  # Переадресация после успешного удаления

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class CommentDeleteView(LoginRequiredMixin, UserCanDeleteMixin, DeleteView):
    """Форма удаления комментария"""
    model = Comment
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        post_id = self.kwargs['post_id']
        return reverse_lazy('post_detail', kwargs={'pk': post_id})

    def get_object(self):
        comment_id = self.kwargs['comment_id']
        return get_object_or_404(
            Comment,
            id=comment_id,
            post_id=self.kwargs['post_id']
        )

    def has_permission(self):
        obj = self.get_object()
        return obj.author == self.request.user


