from django.core.paginator import Paginator
from django.conf import settings


def paginator(request, posts):
    paginator = Paginator(posts, settings.PAGINATOR_COUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
