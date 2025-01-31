#from django import template
from django.contrib.contenttypes import fields
from django.db import models
from django.db.models import Count
from django.forms import formsets
from django.forms.models import modelform_factory
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView, FormView
from django.views.generic.detail import DetailView
from usertype.forms import CourseEnrollForm, UserRegisterForm
from .models import Course, Module, Content, Subject
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import TemplateResponseMixin, View
from .forms import ModuleFormSet
from django.apps import apps

from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseBase

from capstone.settings.base import LOGIN_REDIRECT_URL




# Create your views here.


class OwnerMixin(object):
  def get_queryset(self):
    qs = super().get_queryset()
    return qs.filter(owner=self.request.user)


class OwnerEditMixin(object):
  def form_valid(self, form):
    form.instance.owner = self.request.user
    return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
  model = Course
  fields = ['subject', 'title', 'slug', 'overview']
  success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):  
  template_name = 'courses/manage/course/form.html'

###
class ManageCourseListView(OwnerCourseMixin, ListView):
  #model = Course
  template_name = 'courses/manage/course/list.html'
  permission_required = 'ecollege.view_course'    


###
class CourseCreateView(OwnerCourseEditMixin, CreateView):
  #model = Course
  permission_required = 'ecollege.add_course'    # You need to check if this is correct later
  #pass
  

###
class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
  permission_required = 'ecollege.change_course'    # You need to check if this is correct later
  #pass

###
class CourseDeleteView(OwnerCourseMixin, DeleteView):
  template_name = 'courses/manage/course/delete.html'
  permission_required = 'ecollege.delete_course'    # You need to check if this is correct later


class CourseModuleUpdateView(TemplateResponseMixin, View):
  template_name = 'courses/manage/module/formset.html' 
  course = None

  def get_formset(self, data=None):
    return ModuleFormSet(instance=self.course, data=data)

  def dispatch(self, request, pk):
    self.course = get_object_or_404(Course, id=pk, owner=request.user)
    return super().dispatch(request, pk)


  def get(self, request,  *args, **kwargs):
    formset = self.get_formset()
    return self.render_to_response({'course': self.course, 'formset': formset})


  def post(self, request, *args, **kwargs):
    formset = self.get_formset(data=request.POST)
    if formset.is_valid():
      formset.save()
      return redirect('manage_course_list')
    return self.render_to_response({'course': self.course, 'formset': formset})


class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
          return apps.get_model(app_label='ecollege', model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)


    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)     
        return super().dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form, 'object': self.obj})
                                       

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # new content
                Content.objects.create(module=self.module, item=obj)                                      
            return redirect('module_content_list', self.module.id)

        return self.render_to_response({'form': form, 'object': self.obj})
                                      

class ContentDeleteView(View):
  def post(self, request, id):
    content = get_object_or_404(Content, id=id, module__course__owner=request.user)
    module = content.module
    content.item.delete()
    content.delete()
    return redirect ('module_content_list', module.id)


class ModuleContentListView(TemplateResponseMixin, View):
  template_name = 'courses/manage/module/content_list.html'

  def get(self, request, module_id):
    module = get_object_or_404(Module, id=module_id, course__owner=request.user)
    return self.render_to_response({'module':module})


class CourseListView(TemplateResponseMixin, View):
  model = Course 
  template_name = 'courses/course/list.html'

  def get(self, request, subject=None):
    subjects = Subject.objects.annotate(total_courses=Count('courses'))
    courses = Course.objects.annotate(total_modules=Count('modules'))
    if subject:
      subject = get_object_or_404(Subject, slug=subject)
      courses = courses.filter(subject=subject)
    return self.render_to_response({'subjects':subjects, 'subject':subject, 'courses': courses})


class CourseDetailView(DetailView):
  model = Course
  template_name = 'courses/course/detail.html'
  
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['enroll_form'] = CourseEnrollForm(initial={'course':self.object})
    return context


class IndexView(CourseListView):
  model = Course 
  template_name = 'index.html'

  def get(self, request, subject=None):
    subjects = Subject.objects.annotate(total_courses=Count('courses'))
    courses = Course.objects.annotate(total_modules=Count('modules'))
    if subject:
      subject = get_object_or_404(Subject, slug=subject)
      courses = courses.filter(subject=subject)
    return self.render_to_response({'subjects':subjects, 'subject':subject, 'courses': courses})
