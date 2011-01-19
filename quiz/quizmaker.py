from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response
from django.template import Context, loader
import sys
import re, random
from django.utils import simplejson
import models

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
        cl = models.CategoryLink(triplet=t,category=cat); cl.save()
    cat = models.Category(name='Preterit Tense Regular Verbs')
    cat.save()
    for sp,eng in conjugations.make_verb_quiz(reg_verbs,
                                 conjugations.make_preterit,
                                 conjugations.make_eng_pret):
        t = models.Triplet(l1=eng,l2=sp); t.save()
        cl = models.CategoryLink(triplet=t,category=cat); cl.save()
    return HttpResponseRedirect('/quiz/')
