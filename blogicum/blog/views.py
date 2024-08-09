from django.conf import settings
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from .forms import PostForm, CommentForm
from .models import Post, Category, Comment
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from .models import User


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


def index(request):
    post_list = get_filter_posts()[:settings.POSTS_BY_PAGE]
    context = {'page_obj': post_list}

    return render(request, 'blog/index.html', context)


class PostDetailView(DetailView):

    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comments = Comment.objects.filter(
            post_id=self.object).order_by('created_at')
        context['comments'] = comments
        context['form'] = CommentForm()
        return context
""" def post_detail(request, id):
    post = get_object_or_404(get_filter_posts(), id=id)
    context = {'post': post}

    return render(request, 'blog/detail.html', context)
 """

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
    '''Редактирование поста'''
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'


class DeletePostView(DeleteView):
    '''Удаление поста'''
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class CommetPostView(CreateView):
    model = Post
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
                       kwargs={'post_id': self.kwargs['post_id']})

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
    model = Post
    template_name = 'blog/user.html'
    fields = '__all__'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

class CommentUpdateView(UpdateView):
    model = Comment
    


class CommentDeleteView(DeleteView):
    model = Comment
    
