from django.urls import reverse
from rest_framework import generics
from pipeapp.models import TodoItems
from django.views import View
from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.core import serializers
from django.forms.models import model_to_dict
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers


class BaseMixin:
    def __init__(self):
        self.Model = TodoItems
    def set_up(self):
        self.Model = TodoItems
        self.method = 'get'


class BaseForm(forms.ModelForm, BaseMixin):
    class Meta:
        b = BaseMixin()
        b.set_up()
        model = b.Model
        fields = '__all__'


class ReadMixin(BaseMixin, View):
    def get(self, request):
        b = BaseMixin()
        b.set_up()
        model = b.Model
        data = serializers.serialize("json", model.objects.all())

        return render(request, 'get.html', {'model': data})


class CreateMixin(View):
    def get(self, request):
        get_form = BaseForm()
        return render(request, 'post.html', context={'post_form': get_form})

    def post(self, request):
        post_form = BaseForm(request.POST)
        if post_form.is_valid():
            instance = post_form.save()
            return redirect(instance)
        return render(request, 'post.html', {'post_form': post_form})


class UpdateMixin(View, BaseMixin):
    b = BaseMixin()
    b.set_up()
    Model = b.Model

    def get(self, request, id):
        model = get_object_or_404(self.Model, id=id)
        update_form = BaseForm(instance=model)
        return render(request, 'update.html', {'update_form': update_form})

    def post(self, request, id):
        model = get_object_or_404(self.Model, id=id)
        update_form = BaseForm(request.POST, instance=model)
        if update_form.is_valid():
            model = update_form.save()
            return redirect(model)
        return render(request, 'update.html', {'update_form': update_form})


class DeleteMixin(View, BaseMixin):
    b = BaseMixin()
    b.set_up()
    Model = b.Model

    def get(self, request, id):
        model = get_object_or_404(self.Model, id=id)
        return render(request, 'delete.html', context={'model': model})

    def post(self, request, id):
        model = get_object_or_404(self.Model, id=id)
        model.delete()
        return redirect(reverse('get'))

