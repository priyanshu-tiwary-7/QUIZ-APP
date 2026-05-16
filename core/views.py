from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
import csv
import uuid
from io import TextIOWrapper
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Avg, Max
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import (
    Category,
    Quiz,
    Question,
    Option,
    Result,
    Attempt,
    Answer,
    Certificate
)

@login_required
def home(request):

    categories = Category.objects.all()

    context = {
        'categories': categories
    }

    return render(
        request,
        'core/home.html',
        context
    )

@login_required
def category_quizzes(request, category_id):

    category = Category.objects.get(
        id=category_id
    )

    quizzes = Quiz.objects.filter(
        category=category
    )

    context = {
        'category': category,
        'quizzes': quizzes
    }

    return render(
        request,
        'core/category_quizzes.html',
        context
    )

@login_required
def quiz_page(request, quiz_id):

    quiz = Quiz.objects.get(
        id=quiz_id
    )

    questions = Question.objects.filter(
        quiz=quiz
    )

    score = 0

    if request.method == 'POST':

        for question in questions:

            selected_option = request.POST.get(
                f'question_{question.id}'
            )

            if selected_option:

                option = Option.objects.get(
                    id=selected_option
                )

                if option.is_correct:
                    score += 1

        return render(
            request,
            'core/result.html',
            {
                'score': score,
                'total': questions.count()
            }
        )

    context = {
        'quiz': quiz,
        'questions': questions
    }

    return render(
        request,
        'core/quiz_page.html',
        context
    )
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email    = request.POST['email']
        password = request.POST['password']
        confirm  = request.POST['confirm_password']

        # Check password match
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        # Check username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        return redirect('register')

        # Check email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        return redirect('register')
         
        User.objects.create_user(
         username=username,
         email=email,
         password=password
)
  
  
  
        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'core/register.html')


def login_view(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        # Check username & password
        user = authenticate(
            request,
            username=username,
            password=password
        )

        # If correct
        if user is not None:

            login(request, user)

            messages.success(
                request,
                f"Welcome {username}!"
            )

            return redirect('home')

        # If wrong
        else:

            messages.error(
                request,
                "Invalid username or password."
            )

            return redirect('login')

    return render(request, 'core/login.html')


@login_required
def logout_view(request):

    logout(request)

    messages.info(
        request,
        "You logged out successfully."
    )

@login_required
def start_quiz(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        pk=quiz_id
    )

    questions = quiz.question_set.all()

    request.session['quiz_id'] = quiz_id
    request.session['question_index'] = 0
    request.session['score'] = 0
    request.session['answers'] = {}

    return redirect('attempt_quiz')

@login_required
def attempt_quiz(request):

    quiz_id = request.session.get('quiz_id')

    question_index = request.session.get(
        'question_index',
        0
    )

    quiz = get_object_or_404(
        Quiz,
        pk=quiz_id
    )

    questions = quiz.question_set.all()

    if question_index >= len(questions):
        return redirect('quiz_result')

    current_question = questions[question_index]

    options = current_question.options.all()

    if request.method == 'POST':

        selected_option_id = request.POST.get(
            'option'
        )

        if selected_option_id:

            selected_option = Option.objects.get(
                id=selected_option_id
            )

            request.session['answers'][
                str(current_question.id)
            ] = selected_option.id

            if selected_option.is_correct:
                request.session['score'] += 1

        request.session['question_index'] += 1

        return redirect('attempt_quiz')

    return render(
        request,
        'core/quiz_attempt.html',
        {
            'question': current_question,
            'options': options,
            'question_number': question_index + 1,
            'total_questions': len(questions),
        }
    )

@login_required
def quiz_result(request):

    score = request.session.get(
        'score',
        0
    )

    quiz_id = request.session.get(
        'quiz_id'
    )

    quiz = get_object_or_404(
        Quiz,
        pk=quiz_id
    )

    total_questions = quiz.question_set.count()

    answers = request.session.get(
        'answers',
        {}
    )

    attempt = Attempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total=total_questions,
    )

    for qid, oid in answers.items():

        question = Question.objects.get(
            pk=qid
        )

        option = Option.objects.get(
            pk=oid
        )

        Answer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=option
        )

    Result.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total=total_questions
    )

    Certificate.objects.create(

    user=request.user,

    quiz=quiz,

    score=score,

    total=total_questions,

    certificate_id=str(uuid.uuid4())[:8]
)
    context = {
        'score': score,
        'total_questions': total_questions,
        'quiz': quiz,
    }

    for key in [
        'score',
        'quiz_id',
        'question_index',
        'answers'
    ]:

        request.session.pop(
            key,
            None
        )

    return render(
        request,
        'core/quiz_result.html',
        context
    )

@login_required
def result_history(request):

    results = Result.objects.filter(
        user=request.user
    ).order_by('-created_at')

    context = {
        'results': results
    }

    return render(
        request,
        'core/result_history.html',
        context
    )
@login_required
def leaderboard(request):

    leaderboard_data = Result.objects.values(
        'user__username'
    ).annotate(
        total_score=Sum('score')
    ).order_by(
        '-total_score'
    )

    context = {
        'leaderboard_data': leaderboard_data
    }

    return render(
        request,
        'core/leaderboard.html',
        context
    )

@login_required
def dashboard(request):

    results = Result.objects.filter(
        user=request.user
    )

    total_attempts = results.count()

    total_score = results.aggregate(
        Sum('score')
    )['score__sum']

    average_score = results.aggregate(
        Avg('score')
    )['score__avg']

    best_score = results.aggregate(
        Max('score')
    )['score__max']

    recent_results = results.order_by(
        '-created_at'
    )[:5]

    context = {
        'total_attempts': total_attempts,
        'total_score': total_score,
        'average_score': average_score,
        'best_score': best_score,
        'recent_results': recent_results
    }

    return render(
        request,
        'core/dashboard.html',
        context
    )

@login_required
def my_attempts(request):

    attempts = Attempt.objects.filter(
        user=request.user
    ).order_by(
        '-completed_at'
    )

    return render(
        request,
        'core/my_attempts.html',
        {
            'attempts': attempts
        }
    )

@login_required
def attempt_detail(request, attempt_id):

    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        user=request.user
    )

    answers = Answer.objects.filter(
        attempt=attempt
    )

    context = {
        'attempt': attempt,
        'answers': answers
    }

    return render(
        request,
        'core/attempt_detail.html',
        context
    )

@staff_member_required
def admin_dashboard(request):

    from .models import Quiz, Attempt

    context = {

        'total_users': User.objects.count(),

        'total_quizzes': Quiz.objects.count(),

        'total_attempts': Attempt.objects.count(),

        'top_quizzes': Quiz.objects.annotate(
            attempts=Count('attempt')
        ).order_by('-attempts')[:5],
    }

    return render(
        request,
        'core/admin_dashboard.html',
        context
    )

@staff_member_required
def admin_manage_users(request):

    users = User.objects.all()

    context = {
        'users': users
    }

    return render(
        request,
        'core/admin_users.html',
        context
    )


@staff_member_required
def admin_add_user(request):

    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )

        email = request.POST.get(
            'email'
        )

        password = request.POST.get(
            'password'
        )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

        else:

            User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            messages.success(
                request,
                "User created successfully."
            )

        return redirect(
            'admin_manage_users'
        )

    return render(
        request,
        'core/admin_add_user.html'
    )


@staff_member_required
def delete_user(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id
    )

    user.delete()

    messages.success(
        request,
        "User deleted successfully."
    )

    return redirect(
        'admin_manage_users'
    )


@staff_member_required
def upload_users_csv(request):

    if request.method == 'POST':

        csv_file = request.FILES[
            'csv_file'
        ]

        file_data = TextIOWrapper(
            csv_file.file,
            encoding='utf-8'
        )

        reader = csv.DictReader(
            file_data
        )

        for row in reader:

            username = row['username']

            email = row['email']

            password = row['password']

            if not User.objects.filter(
                username=username
            ).exists():

                User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )

        messages.success(
            request,
            "Users uploaded successfully."
        )

        return redirect(
            'admin_manage_users'
        )

    return render(
        request,
        'core/admin_upload_users.html'
    )


@staff_member_required
def edit_user(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id
    )

    if request.method == 'POST':

        user.username = request.POST.get(
            'username'
        )

        user.email = request.POST.get(
            'email'
        )

        password = request.POST.get(
            'password'
        )

        if password:

            user.set_password(password)

        user.save()

        messages.success(
            request,
            "User updated successfully."
        )

        return redirect(
            'admin_manage_users'
        )

    context = {
        'user': user
    }

    return render(
        request,
        'core/admin_edit_user.html',
        context
    )

@login_required
def my_certificates(request):

    certificates = Certificate.objects.filter(
        user=request.user
    ).order_by(
        '-issued_at'
    )

    context = {
        'certificates': certificates
    }

    return render(
        request,
        'core/my_certificates.html',
        context
    )