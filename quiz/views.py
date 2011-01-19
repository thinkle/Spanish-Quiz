# -*- coding: utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response
from django.template import Context, loader
import sys
import re, random
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
    
def index (request):
    cats = models.Category.objects.all()
    return render_to_response(
        'index.html',
        {'data':cats})

def mc_r (request, category, reverse=False, prev=None, rightanswer=None):
    return mc(request, category, reverse=True, prev=prev, rightanswer=rightanswer)

def mc (request, category, reverse=False, prev=None, rightanswer=None):
    category = int(category)
    cat = models.Category.objects.get(id=category)
    catlinks = models.CategoryLink.objects.filter(category=cat)[:]
    my_links = []
    for cl in catlinks:
        print 'Adding catlink!'
        my_links.append(cl)
    try:
        assert(my_links)
    except AssertionError:
        print "NOT ENOUGH LINKS",my_links,catlinks,category,cat,cat.name
        raise
    random.shuffle(my_links)
    q_a = my_links.pop()
    q_a = q_a.triplet
    all_answers = [o.triplet for o in random.sample(my_links,3)] + [q_a]
    random.shuffle(all_answers)
    answer_rows = [[all_answers[0],all_answers[1]],[all_answers[2],all_answers[3]]]
    print answer_rows
    return render_to_response(
        'simple_quiz.html',
        {'record':(TRIED and '%s/%s'%(CORRECT,TRIED) or ''),
         'category':category,
         'target':q_a,
         'answer_rows':answer_rows,
         'prev':prev,
         'reverse':reverse,
         'rightanswer':rightanswer,
         })

def mc_right (request,category):
    return mc(request,category,prev='right')

def mc_wrong (request,category):
    return mc(request,category,prev='wrong')
         
def mc_answer (request):
    global CORRECT,TRIED
    if request.method == 'POST':
        answer = request.POST['answer']
        category = request.POST['category']
        target = request.POST['target']
        correct_answer = request.POST['correct_answer']        
        reverse = bool(request.POST['reverse'])
        TRIED += 1
        if answer==correct_answer:
            CORRECT += 1
            return mc(request,category=category,reverse=reverse,
                      prev='right')

        else:
            return mc(request,category=category,reverse=reverse,
                      rightanswer=models.Triplet.objects.get(id=target),
                      prev='wrong')



                

