from django.utils import timezone

from .models import Post


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
