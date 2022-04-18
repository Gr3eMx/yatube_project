
from django.http import HttpResponse


# Главная страница
def index(request):
    return HttpResponse('Главная страница')


def group_posts(request):
    return HttpResponse('Список постов')



def post_detail(request, pk):
    return HttpResponse(f'Вот такой url ты вбил {pk}')