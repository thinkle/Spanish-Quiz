from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response
from django.template import Context, loader
import sys
import re, random
from django.utils import simplejson
import models

def select_or_create (klass,**kw):
    try:
        o = klass.objects.get(**kw)
        return o
    except:
        return klass(**kw)
    

def cleanup_old_mistakes ():
    # Delete everything related to old ser/ir which were confusing
    ser_ir_confusion_triplets = models.Triplet.objects.filter(
        l2__in=['fui','fuiste','fue','fuimos','fuisteis','fueron']
        )
    for triplet in ser_ir_confusion_triplets:
        cll = models.CategoryLink.objects.filter(triplet=triplet)
        for cl in cll:
            cl.delete()
        triplet.delete()

def init (*args):
    #for o in models.Category.objects.all(): o.delete()
    #print 'DELTED ALL CATS'
    #for o in models.Triplet.objects.all(): o.delete()
    #print 'DELTED ALL TRIPLETS'    
    #for o in models.CategoryLink.objects.all(): o.delete()
    #print 'DELTED ALL CATLINKS'
    cleanup_old_mistakes()
    allcat = select_or_create(models.Category,name='All Verb Forms')
    allcat.save()
    cat = select_or_create(models.Category,name='Spanish II Semester I Vocabulary')
    cat.save()
    ifi = file('unordered_first_161_words.txt','r')
    for l in ifi.readlines():
        words = l.split(':')
        words = [w.strip() for w in words]
        t = select_or_create(models.Triplet,l1=words[1],l2=words[0]); t.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat)
        cl.save()
    import conjugations
    cat = select_or_create(models.Category,name='Present Tense Regular Verbs')
    cat.save()
    reg_verbs = [('hablar','talk'),('comer','eat'),('bailar','dance'),
                 ('besar','kiss'),('escupir','spit')]
    irreg_verbs = [('poner','put'),
                   ('venir','come'),
                   ('ir','go'),('ser','be'),
                   ('saber','know'),('dar','give'),('ver','see'),('querer','want'),
                   ('poder','can')]
    for sp,eng in conjugations.make_verb_quiz(reg_verbs,
                                 conjugations.make_present,
                                 conjugations.make_eng_present):
        t = select_or_create(models.Triplet,l1=eng,l2=sp); t.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=allcat); cl.save()
    cat2 = select_or_create(models.Category,name='Imperfect and Preterit Irregular Verbs')
    cat2.save()
    cat = select_or_create(models.Category,name='Preterit Tense Regular Verbs')
    cat.save()
    for sp,eng in conjugations.make_verb_quiz(reg_verbs,
                                 conjugations.make_preterit,
                                 conjugations.make_eng_pret):
        t = select_or_create(models.Triplet,l1=eng,l2=sp); t.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat2); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=allcat); cl.save()        
    cat = models.Category(name='Preterit Tense Irregular Verbs')
    cat.save()
    for sp,eng in conjugations.make_verb_quiz(irreg_verbs,
                                 conjugations.make_preterit,
                                 conjugations.make_eng_pret):
        t = select_or_create(models.Triplet,l1=eng,l2=sp); t.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat2); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=allcat); cl.save()        
    cat = select_or_create(models.Category,name='Imperfect Verbs')
    cat.save()
    for sp,eng in conjugations.make_verb_quiz(reg_verbs+[
        ('venir','come'),('poner','put'),('saber','know'),('dar','give'),('querer','want')],
                                 conjugations.make_imperfect,
                                 conjugations.make_eng_past_progr):
        t = select_or_create(models.Triplet,l1=eng,l2=sp); t.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cat2); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=allcat); cl.save()
    psub = select_or_create(models.Category,
                            name='Past Subjunctive/Pasado del subjuntivo'
                            ); psub.save()
    cond = select_or_create(models.Category,name='Conditional/Potencial'); cond.save()
    psub_cond = select_or_create(models.Category,name='Past Subjunctive + Conditional'); psub_cond.save()
    for sp,eng in conjugations.make_verb_quiz(reg_verbs +
                                              [('venir','come'),('poner','put'),('saber','know'),('dar','give'),('querer','want'),('tener','have'),
                                               ('ser','be'),('ir','go')],
                                              conjugations.make_past_subjunctive,
                                              conjugations.make_eng_past_subj):
        t = select_or_create(models.Triplet,l1=eng,l2=sp); t.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=psub_cond); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=psub); cl.save()
    for sp,eng in conjugations.make_verb_quiz(reg_verbs +
                                              [('venir','come'),('poner','put'),('saber','know'),('dar','give'),('querer','want'),('tener','have')],
                                              conjugations.make_conditional,
                                              conjugations.make_eng_cond):
        t = select_or_create(models.Triplet,l1=eng,l2=sp); t.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=psub_cond); cl.save()
        cl = select_or_create(models.CategoryLink,triplet=t,category=cond); cl.save()        
        
    return HttpResponseRedirect('/quiz/')

