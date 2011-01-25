# -*- coding: utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render_to_response
from django.template import Context, loader
from django_openid_auth.models import UserOpenID
from django.contrib.auth.models import User
from django.forms import ModelForm
import sys
import re, random, datetime,time
from django.utils import simplejson
import models

CORRECT = 0
TRIED = 0

vocab_data_set = []
ifi = file('unordered_first_161_words.txt','r')
for l in ifi.readlines():
    words = l.split(':')
    words = [w.strip() for w in words]
    vocab_data_set.append(words)

def init (*args):
    cat = models.Category(name='Spanish II Semester I Vocabulary')
    cat.save()
    ifi = file('unordered_first_161_words.txt','r')
    for l in ifi.readlines():
        words = l.split(':')
        words = [w.strip() for w in words]
        t = models.Triplet(l1=words[1],l2=words[0]); t.save()
        cl = models.CategoryLink(triplet=t,category=cat)
        cl.save()
    import conjugations
    cat = models.Category(name='Present Tense Regular Verbs')
    cat.save()
    reg_verbs = [('hablar','talk'),('comer','eat'),('bailar','dance'),
                 ('besar','kiss'),('escupir','spit')]
    for sp,eng in conjugations.make_verb_quiz(reg_verbs,
                                 conjugations.make_present,
                                 conjugations.make_eng_present):
        print 'Adding',sp,eng
        t = models.Triplet(l1=eng,l2=sp); t.save()
        cl = models.CategoryLink(triplet=t,category=cat)
    cat = models.Category(name='Preterit Tense Regular Verbs')
    cat.save()
    for sp,eng in conjugations.make_verb_quiz(reg_verbs,
                                 conjugations.make_preterit,
                                 conjugations.make_eng_pret):
        t = models.Triplet(l1=eng,l2=sp); t.save()
        cl = models.CategoryLink(triplet=t,category=cat)
    return HttpResponseRedirect('/quiz/')
    
# User stuff

class UserForm (ModelForm):
    class Meta:
        model = User
        fields = ["first_name","last_name","email"]

def logout_user (request):
    logout(request)
    return HttpResponseRedirect('/')

#@login_required
def profile (request):
    if request.method == 'POST':
        uf = UserForm(request.POST,instance=request.user)
        if uf.is_valid():
            uf.save()
        return HttpResponseRedirect('/')
    else:
        uf = UserForm(instance=request.user)
    return render_to_response('profile.html',{'uf':uf})

# Quiz stuff

def index (request):
    cats = models.Category.objects.all()
    return render_to_response(
        'index.html',
        {'data':cats})

def mc_r (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return mc(request, category, reverse=True, rightanswer=rightanswer, lastanswer=lastanswer)

#@login_required
def mc (request, category, reverse=False, rightanswer=None, lastanswer=None):
    try:
        uoid = UserOpenID.objects.get(user=request.user)
    except:
        class o:
            pass
        uoid = o()
        uoid.display_id = 'None'
        uoid.claimed_id=None
    print 'DID:',uoid.display_id,'CID:',uoid.claimed_id
    if uoid.claimed_id:
        TRIED = len(models.QuizData.objects.filter(user=request.user))
        CORRECT = len(models.QuizData.objects.filter(user=request.user,correct=True))
    else:
        global TRIED,CORRECT
    category = int(category)
    cat = models.Category.objects.get(id=category)
    catlinks = models.CategoryLink.objects.filter(category=cat)[:]
    my_links = []
    for cl in catlinks:
        my_links.append(cl)
    try:
        assert(my_links)
    except AssertionError:
        print "NOT ENOUGH LINKS",my_links,catlinks,category,cat,cat.name
        raise
    random.shuffle(my_links)
    q_a = my_links.pop()
    q_a = q_a.triplet
    # Very lame attempt to make choices harder (more similar to each other)
    #my_similar_links = filter(lambda x: x.triplet.l2.startswith(q_a.l2[0]), my_links)
    #if len(my_similar_links) >= 3:
    #    my_links = my_similar_links
    all_answers = [o.triplet for o in random.sample(my_links,3)] + [q_a]
    random.shuffle(all_answers)
    answer_rows = [[all_answers[0],all_answers[1]],[all_answers[2],all_answers[3]]]
    return render_to_response(
        'simple_quiz.html',
        {'record':(TRIED and '%s/%s'%(CORRECT,TRIED) or ''),
         'category':category,
         'target':q_a,
         'answer_rows':answer_rows,
         'reverse':reverse,
         'rightanswer':rightanswer,
         'time':time.time(),
         'lastanswer':lastanswer,
         'user':request.user,
         'uoid':uoid.display_id,
         })

def mc_answer (request):
    if request.method == 'POST':
        global TRIED,CORRECT
        answer = request.POST['answer']
        category = request.POST['category']
        target = request.POST['target']
        correct_answer = request.POST['correct_answer']        
        reverse = request.POST['reverse']
        atime = request.POST['time']
        atime = float(atime)
        current_time = time.time()
        speed = current_time - atime
        if reverse=='False': reverse = False
        else: reverse = True
        try:
            qd = models.QuizData(user=request.user,
                             triplet=models.Triplet.objects.get(id=target),
                             reverse=reverse,
                             correct=(answer==correct_answer),
                             speed=speed,
                             answer_time=datetime.datetime.today(),

                             )
        except:
            qd = models.QuizData(
                             triplet=models.Triplet.objects.get(id=target),
                             reverse=reverse,
                             correct=(answer==correct_answer),
                             speed=speed,
                             answer_time=datetime.datetime.today(),
                             )
        
        qd.save()
        TRIED += 1
        if answer==correct_answer:
            CORRECT += 1
            prev='right'
        else:
            prev='wrong'
        return mc(request,category=category,reverse=reverse,rightanswer=models.Triplet.objects.get(id=target),
                  lastanswer=qd)
    else:
        return HttpResponseRedirect('/')



                

