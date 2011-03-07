from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.forms import ModelForm, ModelChoiceField
import models
from quizmaker import select_or_create

def uploader (request):
    return render_to_response('uploader.html',{})

class CategoryForm (ModelForm):
    class Meta:
        model = models.Category

class QuizGroupLink (ModelForm):
    class Meta:
        model = models.QuizGroupLink


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
        return HttpResponseRedirect('/new/')
    else:
        mf = CategoryForm()
        return render_to_response('form.html',
                                  {'title':'Category',
                                   'form':mf,
                                   'errors':errors,
                                   'desc':'Create new category',
                                   'action':'/new/category/'}
                                  )

def new_quizgrouplink (request,errors=None):
    if request.method == 'POST':
        instance = models.QuizGroupLink()
        mf = QuizGroupLink(request.POST,instance=instance)
        if mf.is_valid():
            mf.save()
            print 'SAVE!'
        else:
            print 'ERROR!'
            request.method = None
            return new_quizgrouplink(request,errors=mf.errors)
        return HttpResponseRedirect('/new/')
    else:
        mf = QuizGroupLink()
        return render_to_response('form.html',
                                  {'title':'Quizgrouplink',
                                   'form':mf,
                                   'errors':errors,
                                   'desc':'Create new quizgrouplink',
                                   'action':'/new/qg/'}
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
            return HttpResponseRedirect('/new/')
        else:
            print tf.errors
            return HttpResponseRedirect('/new/triplets/')
        return HttpResponseRedirect('/new/')
    else:
        tf = TripletsForm()
        return render_to_response('form.html',
                                  {'title':'Upload Set of Triplets',
                                   'form':tf,
                                   'desc':'Create new quiz',
                                   'action':'/new/triplets/'}
                                  )
    
class SequenceForm (ModelForm):
    parent = ModelChoiceField(queryset=models.Sequence.objects.all(),empty_label='None')
    parent.blank = True
    parent.required = False

    class Meta:
        model = models.Sequence


class SequenceItemForm (ModelForm):

    prev = ModelChoiceField(queryset=models.SequenceItem.objects.all(), empty_label='None (First item)')
    prev.required = False

    class Meta:
        model = models.SequenceItem

def new_sequence (request, errors=None):
    if request.method == 'POST':
        instance = models.Sequence()
        mf = SequenceForm(request.POST,instance=instance)
        #if not mf.cleaned_data['parent']: mf.cleaned_data['parent'] = None
        if mf.is_valid():
            mf.save()
            print 'SAVE!'
        else:
            print 'ERROR!'
            request.method = None
            return new_sequence(request,errors=mf.errors)
        return HttpResponseRedirect('/new/')
    else:
        mf = SequenceForm()
        return render_to_response('form.html',
                                  {'title':'Sequence',
                                   'form':mf,
                                   'errors':errors,
                                   'desc':'Create new sequence',
                                   'action':'/new/sequence/'}
                                  )

def new_sequenceitem (request, errors=None):
    if request.method == 'POST':
        instance = models.SequenceItem()
        mf = SequenceItemForm(request.POST,instance=instance)
        if mf.is_valid():
            mf.save()
            print 'SAVE!'
        else:
            print 'ERROR!'
            request.method = None
            return new_sequenceItem(request,errors=mf.errors)
        return HttpResponseRedirect('/new/')
    else:
        mf = SequenceItemForm()
        return render_to_response('form.html',
                                  {'title':'SequenceItem',
                                   'form':mf,
                                   'errors':errors,
                                   'desc':'Create new item in sequence',
                                   'action':'/new/sequenceitem/'}
                                  )

def append_sequence_items (request, errors=None):
    if request.method == 'POST':
        form = AppendMultipleSequencesForm(request.POST)
        if form.is_valid():
            cat = form.cleaned_data['category']
            seq = form.cleaned_data['sequence']            
            # We begin with reverse by default...
            # Get last item in this sequence
            previous_items = models.SequenceItem.objects.filter(sequence=seq).order_by('-id')
            if previous_items:
                last = previous_items[0]
                really_last = False
                while not really_last:
                    try:
                        obj = models.SequenceItem.objects.get(prev=last)
                    except:
                        really_last = True
                    else:
                        if obj:
                            last = obj
                        else:
                            really_last = True
            else:
                last = None
            for typ in ['reverse','normal','open']:
                if form.cleaned_data['%s_min'%typ]:
                    si = models.SequenceItem()
                    si.minimum_problems = form.cleaned_data['%s_min'%typ]
                    si.maximum_problems = form.cleaned_data['%s_max'%typ]
                    si.threshold = form.cleaned_data['%s_threshold'%typ]
                    si.category = cat
                    si.sequence = seq
                    if typ == 'reverse':
                        si.reverse = True
                    if typ != 'open':
                        si.question_type = models.MULTIPLE_CHOICE
                    else:
                        si.question_type = models.OPEN_RESPONSE
                    si.prev = last
                    si.save()
                    last = si
            HttpResponseRedirect('/new/append_seq/')
        else: # if invalid
            print 'ERRORS',form.errors
            errors = form.errors
    form = AppendMultipleSequencesForm({
        'reverse_min':10,
        'reverse_max':100,
        'reverse_threshold':0.95,
        'normal_min':10,
        'normal_max':100,
        'normal_threshold':0.9,
        'open_min':10,
        'open_max':30,
        'open_threshold':0.8,
        })
    return render_to_response('form.html',
                              {'title':'Append Sequence Item(s)',
                               'form':form,
                               'errors':errors,
                               'desc':'Append items to sequence',
                               'action':'/new/append_seq/'}
                              )

class AppendMultipleSequencesForm (forms.Form):
    sequence = forms.ModelChoiceField(queryset=models.Sequence.objects.all())
    category = forms.ModelChoiceField(queryset=models.Category.objects.all())
    reverse_min = forms.IntegerField()
    reverse_max = forms.IntegerField()    
    reverse_threshold = forms.FloatField(max_value=1,min_value=0)
    normal_min = forms.IntegerField()
    normal_max = forms.IntegerField()    
    normal_threshold = forms.FloatField(max_value=1,min_value=0)
    open_min = forms.IntegerField()
    open_max = forms.IntegerField()
    open_threshold = forms.FloatField(max_value=1,min_value=0)

    
