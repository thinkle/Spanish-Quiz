from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.forms import ModelForm
import models
from quizmaker import select_or_create

class CategoryForm (ModelForm):
    class Meta:
        model = models.Category

def new_category (request,errors=None):
    if request.method == 'POST':
        instance = models.Category()
        mf = CategoryForm(request.POST,instance=instance)
        if mf.is_valid():
            mf.save()
            print 'SAVE!'
        else:
            print 'ERROR!'
            request.method = None
            return new_category(request,errors=mf.errors)
        return HttpResponseRedirect('/')
    else:
        mf = CategoryForm()
        return render_to_response('form.html',
                                  {'title':'Category',
                                   'form':mf,
                                   'errors':errors,
                                   'desc':'Create new category',
                                   'action':'/new/category/'}
                                  )
    

class TripletsForm (forms.Form):
    category = forms.ModelChoiceField(queryset=models.Category.objects.all())
    csv_file = forms.FileField()

def new_triplets (request):
    if request.method == 'POST':
        tf = TripletsForm(request.POST,request.FILES)
        if tf.is_valid():
            print 'VALID!!!'
            print 'WE DONT DO ANTYHING YET THOUGH'
            print dir(tf)
            print tf.cleaned_data
            print tf.cleaned_data['category']
            print tf.cleaned_data['csv_file']            
            print request.FILES['csv_file']
            ignored = []
            for l in tf.cleaned_data['csv_file'].readlines():
                try:
                    l = l.decode('utf-8')
                except:
                    l = l.decode('iso8859_15')
                if not ':' in l:
                    ignored.append(l)
                else:
                    words = l.split(':')
                    if len(words)==3:
                        l1=words[2].strip()
                        desc=words[1].strip()
                        l2=words[0].strip()
                    else:
                        l1=words[1].strip()
                        l2=words[0].strip()
                        desc=''
                t = select_or_create(models.Triplet,l1=l1,l2=l2,notes=desc); t.save()
                cl = select_or_create(models.CategoryLink,triplet=t,category=tf.cleaned_data['category']); cl.save()
                print 'Saved link between',t,'and',cl
            print 'Ignored: ',ignored
            return HttpResponseRedirect('/')
        else:
            print tf.errors
            return HttpResponseRedirect('/new/triplets/')
        return HttpResponseRedirect('/')
    else:
        tf = TripletsForm()
        return render_to_response('form.html',
                                  {'title':'Upload Set of Triplets',
                                   'form':tf,
                                   'desc':'Create new quiz',
                                   'action':'/new/triplets/'}
                                  )
    
