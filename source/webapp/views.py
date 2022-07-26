from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import TemplateView, RedirectView, FormView, ListView
from webapp.models import Task
from webapp.forms import TaskForm, SearchForm
from webapp.base_view import FormView as CustomFormView


class IndexView(ListView):
    model = Task
    template_name = "index.html"
    context_object_name = "tasks"
    ordering = "-updated_at"
    paginate_by = 5

    def get(self, request, *args, **kwargs):
        self.form = self.get_search_form()
        self.search_value = self.get_search_value()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.search_value:
            return Task.objects.filter(Q(author__icontains=self.search_value) | Q(summary__icontains=self.search_value))
        return Task.objects.all()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["form"] = self.form
        if self.search_value:
            query = urlencode({'search': self.search_value})
            context["query"] = query
            context["search"] = self.search_value
        return context

    def get_search_form(self):
        return SearchForm(self.request.GET)

    def get_search_value(self):
        if self.form.is_valid():
            return self.form.cleaned_data.get("search")


class MyRedirectView(RedirectView):
    url = "https://www.google.ru/"


class TaskView(TemplateView):
    template_name = "task_view.html"

    def get_context_data(self, **kwargs):
        pk = kwargs.get("pk")
        task = get_object_or_404(Task, pk=pk)
        kwargs["task"] = task
        return super().get_context_data(**kwargs)


def index_view_partial(request, create_task_form, status):
    search_form = SearchForm(data=request.GET)
    tasks = Task.objects.all()
    if search_form.is_valid():
        search_value = search_form.cleaned_data.get("search")
        tasks = tasks.filter(summary__contains=search_value)
    tasks = tasks.order_by("-updated_at")
    context = {"tasks": tasks, "search_form": search_form, "create_task_form": create_task_form}
    return render(request, "index.html", context, status=status)


class CreateTask(CustomFormView):
    form_class = TaskForm
    template_name = "create.html"

    def form_valid(self, form):
        self.task = form.save()
        return super().form_valid(form)

    def get_redirect_url(self):
        return redirect("task_view", pk=self.task.pk)


class UpdateTask(FormView):
    form_class = TaskForm
    template_name = "update.html"

    def dispatch(self, request, *args, **kwargs):
        self.task = self.get_objects()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("task_view", kwargs={"pk": self.task.pk})

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['instance'] = self.task
        return form_kwargs

    def form_valid(self, form):
        self.task = form.save()
        return super().form_valid(form)

    def get_objects(self):
        return get_object_or_404(Task, pk=self.kwargs.get("pk"))


def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "GET":
        pass
        return render(request, "delete.html", {"task": task})
    else:
        task.delete()
        return redirect("index")
