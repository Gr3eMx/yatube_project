
from django.http import HttpResponse
from django.shortcuts import render


# Главная страница
def index(request):
    text = 'Это главная страница проекта Yatube'
    template = 'posts/index.html'
    context = {
        'text': text,
    }
    return render(request, template, context)

def group_posts(request):
    text = 'Здесь будет информация о группах проекта Yatube'
    template = 'posts/group_list.html'
    context = {
        'text': text,
    }
    return render(request, template, context)



def post_detail(request, pk):
    return HttpResponse(f'Вот такой url ты вбил {pk}')