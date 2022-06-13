from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post

User = get_user_model()


def index(request):
    POSTS_COUNT: int = 10

    post_list = Post.objects.select_related('author', 'group')
    paginator = Paginator(post_list, POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'posts/index.html',
        {'page_obj': page_obj}
    )


def group_posts(request, slug):
    POSTS_COUNT: int = 10

    group = get_object_or_404(Group, slug=slug)

    post_list = group.posts.select_related('author')
    paginator = Paginator(post_list, POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': page_obj}
    )


def profile(request, username):
    POSTS_COUNT: int = 10

    user = get_object_or_404(User, username=username)
    post_list = user.posts.select_related('group')
    post_count = post_list.count
    paginator = Paginator(post_list, POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    full_name = user.get_full_name()

    context = {
        'username': user,
        'full_username': full_name,
        'page_obj': page_obj,
        'post_count': post_count
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('author')

    form = CommentForm(request.POST or None)
    author = post.author

    if request.user == author:
        is_edit = True
    else:
        is_edit = False

    post_count = Post.objects.filter(author=author).count()
    context = {
        'username': author.username,
        'full_username': author.get_full_name(),
        'post': post,
        'post_count': post_count,
        'is_edit': is_edit,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    is_edit = False

    if not request.method == 'POST':
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': is_edit}
        )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': is_edit}
        )

    post: Post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user == post.author:
        is_edit = True
    else:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if not request.method == 'POST':
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': is_edit, 'post': post}
        )

    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': is_edit, 'post': post}
        )

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
