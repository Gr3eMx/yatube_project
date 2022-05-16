from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect, reverse
from .models import Post, Group, User
from django.contrib.auth.decorators import login_required
from .forms import PostForm


# Главная страница
def index(request):
    post_list = Post.objects.order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author).order_by('-pub_date')
    count = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'count': count,
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    text = post.text[:30]
    author = post.author
    count = Post.objects.filter(author=author).count()
    context = {
        'post': post,
        'author': author,
        'count': count,
        'text': text,

    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post = form.save()
        username = request.user
        return redirect(reverse('posts:profile', kwargs={
                    'username': username})
            )
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    is_edit = True
    if request.user != post.author:
        return redirect(f'/posts/{post_id}/')
    if form.is_valid():
        post = form.save(commit=False)
        form.save()
        return redirect(f'/posts/{post_id}/')
    return render(request, 'posts/create_post.html', {'form': form, 'is_edit': is_edit})
