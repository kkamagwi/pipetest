from django.utils.decorators import classonlymethod
from functools import update_wrapper
import typing as t
from rest_framework import viewsets
from rest_framework import serializers
from django.db import migrations
from frozendict import frozendict
from pipe.core.base import BasePipe, Step
from pipe.server.wrappers import PipeRequest, PipeResponse, make_response

from pipe.generics.helpers import TLambda, TPutDefaults
from pipe.server import HTTPPipe
from pipe.server.http.extract import EFormData
from pipe.server.http.load import LResponse
from .src.template.transform import TTemplateResponseReady
from pipe.generics.db.orator_orm.load import LDBInsertUpdateBase, LDatabaseDeleteBase

from pipe.core.decorators import configure
from django.conf import settings
from pipe.generics.db.orator_orm.extract import EDBReadBase



@configure({'connection_config': settings.DATABASES})
class EDatabase(EDBReadBase):
    pass

@configure({'connection_config': settings.DATABASES})
class LDatabase(LDBInsertUpdateBase):
    pass

@configure({'connection_config': settings.DATABASES})
class LDelete(LDatabaseDeleteBase):
    pass

class DjangoViewPipe(BasePipe):

    """Pipe structure for the `server` package.

    Pipe structure. Contains two parts - pipe for request and pipe for response.
    Data goes in next way
    (in): request extractor -> request transformer -> request loader
    (out): response extractor -> response transformer -> response loader

    Example:


    ```python
    @app.route('/todo/')
    class TodoResource(HTTPPipe):
    pipe_schema = {
        'GET': {
            'out': (
                EDatabase(table_name='todo-items'), TJsonResponseReady(data_field='todo-items_list'), LJsonResponse()
            )
        },
        'POST': {
            'in': (EJsonBody(), LDatabase(data_field='json', table_name='todo-items')),
            'out': (
                TLambda(lambda_=lambda store: store.copy(id=store.get('todo-items_insert'))),
                EDatabase(table_name='todo-items'), TJsonResponseReady(data_field='todo-items_item'), LJsonResponse()
            )
        }
    }
    ```


    """
    pipe_schema: t.Dict[str, t.Dict[str, t.Iterable[Step]]] = {}

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in kwargs.items():
            setattr(self, key, value)

    def create_pipe(self, request, initial, *args, **kwargs):
        self.__request = request

        super(HTTPPipe, self).__init__(dict(request=request, **initial), *args, **kwargs)

    @property
    def request(self) -> PipeRequest:
        """Getter for request object
        """
        return self.__request

    def interrupt(self, store) -> bool:
        # If some step returned response, we should interrupt `pipe` execution
        return issubclass(store.__class__, PipeResponse) or isinstance(store, PipeResponse)

    def run_pipe(self) -> frozendict:
        """The main method.
        Takes data and pass through pipe. Handles request and response

        :raises: PipeException
        """
        pipe_to_run = self.pipe_schema.get(self.request.method, None)

        if pipe_to_run is None:
            return make_response('method isn\'t supported', status=400)

        self._run_pipe(pipe_to_run.get('in', ()))
        return self._run_pipe(pipe_to_run.get('out', ()))
    """
    Intentionally simple parent class for all views. Only implements
    dispatch-by-method and simple sanity checking.
    """

    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    @classonlymethod
    def as_django_view(cls, actions=None, **initkwargs):
        """Main entry point for a request-response process."""
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(
                    'The method name %s is not accepted as a keyword argument '
                    'to %s().' % (key, cls.__name__)
                )
            if not hasattr(cls, key):
                raise TypeError("%s() received an invalid keyword %r. as_view "
                                "only accepts arguments that are already "
                                "attributes of the class." % (cls.__name__, key))
            if not actions:
                raise TypeError("The `actions` argument must be provided when "
                                "calling `.as_view()` on a ViewSet. For example "
                                "`.as_view({'get': 'list'})`")

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            self.setup(request, *args, **kwargs)
            if not hasattr(self, 'request'):
                raise AttributeError(
                    "%s instance has no 'request' attribute. Did you override "
                    "setup() and forget to call super()?" % cls.__name__
                )
            return self.dispatch(request, *args, **kwargs)

        view.view_class = cls
        view.view_initkwargs = initkwargs
        view.actions = actions
        # take name and docstring from class
        update_wrapper(view, cls, updated=())
        return view

    def setup(self, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        if hasattr(self, 'get') and not hasattr(self, 'head'):
            self.head = self.get
        self.request = self.request
        self.args = args
        self.kwargs = kwargs

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    def initialize_request(self, request, *args, **kwargs):
        """
        Set the `.action` attribute on the view, depending on the request method.
        """
        request = super().initialize_request(request, *args, **kwargs)
        method = request.method.lower()
        if method == 'options':
            # This is a special case as we always provide handling for the
            # options method in the base `View` class.
            # Unlike the other explicitly defined actions, 'metadata' is implicit.
            self.action = 'metadata'
        else:
            self.action = self.action_map.get(method)
        return request


class FormPage(DjangoViewPipe):

    pipe_schema = {
        'GET': {
            'out': (
                EDatabase(table_name='todo-items'),
                TLambda(lambda_=lambda store: frozendict(context=dict(
                    items=store.get('todo-items_list')))),
                TTemplateResponseReady(template_name='index.html'),
                LResponse(data_field='template', headers={'Content-Type': 'text/html'})
            ),
        },
        'POST': {
            'in': (
                EFormData(),
                TPutDefaults(defaults={
                    'done': False
                }, field_name='form'),
                LDatabase(data_field='form', table_name='todo-items')
            ),
            'out': (
                EDatabase(table_name='todo-items'),
                TLambda(lambda_=lambda store: frozendict(
                    context=dict(items=store.get('todo-items_list'))
                )),
                TTemplateResponseReady(template_name='index.html'),
                LResponse(data_field='template', headers={'Content-Type': 'text/html'})
            )
        }
    }

    def create_pipe(request, initial):
        initial = FormPage.pipe_schema