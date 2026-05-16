from django.contrib import admin

from .models import (
    Category,
    Quiz,
    Question,
    Option,
    Attempt,
    Answer,
    Certificate
)

from django.contrib.auth.models import User


# Inline for adding options directly inside question
class OptionInline(admin.TabularInline):

    model = Option
    extra = 2
    max_num = 4


# Question Admin
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        'text',
        'quiz'
    )

    inlines = [OptionInline]


# Quiz Admin
class QuizAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'category',
        'created_at'
    )

    list_filter = (
        'category',
    )


# Attempt Admin
class AttemptAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'quiz',
        'score',
        'total',
        'completed_at'
    )

    list_filter = (
        'quiz',
        'user'
    )

    search_fields = (
        'user__username',
        'quiz__title'
    )


# Answer Admin
class AnswerAdmin(admin.ModelAdmin):

    list_display = (
        'attempt',
        'question',
        'selected_option'
    )


# Register models
admin.site.register(Category)

admin.site.register(
    Quiz,
    QuizAdmin
)

admin.site.register(
    Question,
    QuestionAdmin
)

admin.site.register(
    Attempt,
    AttemptAdmin
)

admin.site.register(
    Answer,
    AnswerAdmin
)

admin.site.register(Certificate)