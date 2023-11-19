from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from .models import User

class UserCreationForm(DjangoUserCreationForm):

    class Meta:
        model = User
        fields = ("email",)

class UserChangeForm(DjangoUserChangeForm):

    class Meta:
        model = User
        fields = "__all__"