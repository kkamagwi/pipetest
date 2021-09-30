from django.urls import reverse
from rest_framework import generics
from .models import TodoItems
from django.views import View
from django import forms
from django.shortcuts import get_object_or_404, render, redirect

# transforn необходим для изменения, он дает возможность перезапись frozendickt
# extract извлекает данные разных форматов json, form, dickt
# load проверяет на ошибки, валидирует, отправляет на страницу

# class FormPage(HTTPPipe):
#     pipe_schema = {
#         'GET': {
#             'out': (
#                 EDatabase(table_name='todo-items'),
#                 TLambda(lambda_=lambda store: frozendict(context=dict(
#                     items=store.get('todo-items_list')))),
#                 TTemplateResponseReady(template_name='index.html'),
#                 LResponse(data_field='template', headers={'Content-Type': 'text/html'})
#             ),
#         },
#         'POST': {
#             'in': (
#                 EFormData(),
#                 TPutDefaults(defaults={
#                     'done': False
#                 }, field_name='form'),
#                 LDatabase(data_field='form', table_name='todo-items')
#             ),
#             'out': (
#                 EDatabase(table_name='todo-items'),
#                 TLambda(lambda_=lambda store: frozendict(
#                     context=dict(items=store.get('todo-items_list'))
#                 )),
#                 TTemplateResponseReady(template_name='index.html'),
#                 LResponse(data_field='template', headers={'Content-Type': 'text/html'})
#             )
#         }
#     }
