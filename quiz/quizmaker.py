# -*- coding: utf-8

from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response
from django.template import Context, loader
import sys
import re, random
from django.utils import simplejson
import models
import conjugations

def select_or_create (klass,**kw):
    try:
        o = klass.objects.get(**kw)
        return o
    except:
        return klass(**kw)
    

def cleanup_old_mistakes ():
    return
    # Delete everything related to old ser/ir which were confusing
    ser_ir_confusion_triplets = models.Triplet.objects.filter(
        l2__in=[u'fui',u'fuiste',u'fue',u'fuimos',u'fuisteis',u'fueron']
        )
    for triplet in ser_ir_confusion_triplets:
        cll = models.CategoryLink.objects.filter(triplet=triplet)
        for cl in cll:
            cl.delete()
        triplet.delete()


# ALL_VERB_FORMS
# Indicative -> Past Time Frame -> Preterit (Preterit Regular + Preterit Irregular), Imperfect, Pluperfect
# Indicative -> Present Time Frame -> Present (Regular + Irregular)
# Indicative -> Compound Forms -> Present Perfect, Pluperfect
# Subjunctive -> Present Subjunctive (Regular + Irregular) + Past subjunctive
# All Verb Forms -> Indicative + Subjunctive
#

def crawl_categories (name, children=[], parent=None, cdic={}):
    cdic[name] = models.Category(name=name)
    print u'Creating category',name,u'parent',parent
    cdic[name].save()
    if parent:
        cdic[name].parent = parent
        cdic[name].save()
    for child,grandchildren in children:
        crawl_categories(child,grandchildren,parent=cdic[name],cdic=cdic)

def add_verbs (verblist, spanish_func, english_func, category):
    print u'Creating verbs for u',category.name
    for sp,eng in conjugations.make_verb_quiz(verblist, spanish_func, english_func):
        t = select_or_create(models.Triplet,l1=eng,l2=sp)
        t.save()
        cl = models.CategoryLink(triplet=t,category=category)
        cl.save()
    print u'Done!'

def verb_forms ():
    u'''Create verb form quizzes'''
    data = [
        (u'Indicative',
         [(u'Past Tense Verbs',[(u'Preterit Tense Verbs',[(u'Preterit Tense Regular Verbs',[]),
                                                        (u'Preterit Tense Irregular Verbs',[]),
                                ]
                    ),
                   (u'Imperfect Verbs',[(u'Imperfect Regular Verbs',[]),
                                       (u'Imperfect Irregular Verbs',[]),
                                       ]),
                   ]),
          (u'Present Tense Verbs',[(u'Present Tense Irregular Verbs',[]),
                      (u'Present Tense Regular Verbs',[]),
                      (u'Present Tense Stem-Changers',[]),
                      ]
           ),
          #(u'Future',[#(u'Popular Future',[]),
          #           (u'Future',[
          #               (u'Future Regular',[])
          #               (u'Future Irregular',[]),
          #               ]
          #            ),
          #           ]
          # ),
          (u'Conditional Verbs',[(u'Conditional Regular Verbs',[]),
                          (u'Conditional Irregular Verbs',[]),
                          ]
           ),
          (u'Compound Tenses',[
              (u'Antepresente',[]),
              (u'Antepasado',[]),
              #(u'Antefuturo',[]),              
              #(u'Antepotencial',[]),
              ]),
          ]
         ), # End indicative
        (u'Subjunctive',[
            (u'Present Subjunctive',[
                (u'Present Subjunctive Irregular Verbs',[]),
                (u'Present Subjunctive Regular Verbs',[]),
                ]),
            (u'Past Subjunctive Verbs',[]),
            (u'Subjunctive Compound Tenses',[
                (u'Subjunctive Antepresente',[]),
                (u'Subjunctive Antepasado',[]),
                ]
             ),
            ]
         )
        ]
    cdic = {}
    for c,children in data:
        crawl_categories(c,children,cdic=cdic)
    print cdic
    reg_verbs = [(u'hablar',u'talk'),(u'comer',u'eat'),(u'bailar',u'dance'),
                 (u'besar',u'kiss'),(u'escupir',u'spit')]

    # Present Regular
    add_verbs(reg_verbs,conjugations.make_present,conjugations.make_eng_present,cdic[u'Present Tense Regular Verbs'])
    # Present Stem-Changers
    add_verbs([(u'jugar',u'play'),
               (u'sentir',u'feel'),
               (u'poder',u'can'),
               (u'sentar',u'sit'),
               (u'querer',u'want')],conjugations.make_present,conjugations.make_eng_present,cdic[u'Present Tense Stem-Changers'])    
    # Present Irregular
    irreg_verbs = [(u'poner',u'put'),(u'decir',u'say'),
                   (u'venir',u'come'),
                   (u'ir',u'go'),(u'ser',u'be (identity)'),(u'estar',u'be (condition)'),
                   (u'saber',u'know'),(u'dar',u'give'),(u'ver',u'see'),(u'querer',u'want'),
                   (u'poder',u'can')]
    add_verbs(irreg_verbs,conjugations.make_present,conjugations.make_eng_present,cdic[u'Present Tense Irregular Verbs'])
    # Preterit Regular
    add_verbs(reg_verbs,conjugations.make_preterit,conjugations.make_eng_pret,cdic[u'Preterit Tense Regular Verbs'])
    # Preterit Irregular
    add_verbs(irreg_verbs,conjugations.make_preterit,conjugations.make_eng_pret,cdic[u'Preterit Tense Irregular Verbs'])
    # Imperfect Regular
    add_verbs(reg_verbs+[(u'salir',u'exit'),(u'entrar',u'enter'),(u'venir',u'come'),(u'poner',u'put'),(u'saber',u'know'),(u'dar',u'give'),(u'querer',u'want')],
              conjugations.make_imperfect,conjugations.make_eng_past_progr,cdic[u'Imperfect Regular Verbs'])
    # Imperfect Irregular
    add_verbs([(u'ser',u'be (identity)'),(u'ir',u'go')],
              conjugations.make_imperfect,conjugations.make_eng_past_progr,cdic[u'Imperfect Irregular Verbs'])
    # Future Regular
    # add_verbs(irreg_verbs,conjugations.make_preterit,conjugations.make_eng_pret,cdic[u'Preterit Irregular'])        
    # Future Irregular
    # Conditional Regular
    add_verbs(reg_verbs,conjugations.make_conditional,conjugations.make_eng_cond,cdic[u'Conditional Regular Verbs'])
    # Conditional Irregular
    add_verbs([
        (u'venir',u'come'),(u'poner',u'put'),(u'saber',u'know'),(u'querer',u'want'),(u'tener',u'have'),
        (u'hacer',u'make'),(u'decir',u'say')
        ]
        ,conjugations.make_conditional,conjugations.make_eng_cond,cdic[u'Conditional Irregular Verbs'])    
    # Antepresente
    add_verbs(
        reg_verbs + irreg_verbs,
        conjugations.make_antepresente,conjugations.make_eng_present_perfect,
        cdic[u'Antepresente']
        )
    # Antepasado
    add_verbs(
        reg_verbs + irreg_verbs,
        conjugations.make_antepasado,conjugations.make_eng_pluperfect,
        cdic[u'Antepasado']
        )    
    # Antefuturo    
    # Antepotencial
    # Present Subjunctive Irregular
    add_verbs([(u'ser',u'be (identity)'),(u'ver',u'see'),(u'ir',u'go'),(u'estar',u'be (condition)')],
              conjugations.make_present_subjunctive,
              conjugations.make_eng_present_subjunctive,
              cdic[u'Present Subjunctive Irregular Verbs'])
    # Present Subjunctive Regular
    add_verbs(reg_verbs,
              conjugations.make_present_subjunctive,
              conjugations.make_eng_present_subjunctive,
              cdic[u'Present Subjunctive Regular Verbs'])
    # Past Subjunctive
    add_verbs(reg_verbs + [(u'venir',u'come'),(u'poner',u'put'),(u'saber',u'know'),(u'dar',u'give'),(u'querer',u'want'),(u'tener',u'have'),
                           (u'ser',u'be'),(u'ir',u'go')],
              conjugations.make_past_subjunctive,
              conjugations.make_eng_past_subj,cdic[u'Past Subjunctive Verbs'])
    # Subjunctive Antepresente
    add_verbs(
        reg_verbs + irreg_verbs,
        conjugations.make_antepresente_subjuntivo,conjugations.make_eng_present_perfect_subj,
        cdic[u'Subjunctive Antepresente']
        )
    # Subjunctive Antepasado
    add_verbs(
        reg_verbs + irreg_verbs,
        conjugations.make_antepasado_subjuntivo,conjugations.make_eng_pluperfect_subj,
        cdic[u'Subjunctive Antepasado']
        )

def make_quiz (name, categories, description=None):
    qg = select_or_create(models.QuizGroup, name=name)
    if description:
        qg.description = description
    qg.save()
    allc = models.Category(name=name+u' (all)'); allc.save()
    for c in categories:
        qgl = select_or_create(models.QuizGroupLink, category=c, quizgroup=qg)
        qgl.save()
        for cl in models.CategoryLink.objects.filter(category=c):
            new_cl = models.CategoryLink(
                category=allc,
                triplet=cl.triplet
                ); new_cl.save()
    qgl = select_or_create(models.QuizGroupLink, category=allc, quizgroup=qg)
    qgl.save()
    
def init (*args):
    models.Category.objects.all().delete()
    print u'DELTED ALL CATS'
    #for o in models.Triplet.objects.all(): o.delete()
    #print u'DELTED ALL TRIPLETS'    
    models.CategoryLink.objects.all().delete()
    print u'DELTED ALL CATLINKS'
    cleanup_old_mistakes()
    cat = models.Category(name=u'Spanish II Semester I Vocabulary')
    cat.save()
    ifi = file(u'unordered_first_161_words.txt',u'r')
    for l in ifi.readlines():
        words = l.split(':')
        words = [w.strip() for w in words]
        t = select_or_create(models.Triplet,l1=words[1],l2=words[0]); t.save()
        cl = models.CategoryLink(triplet=t,category=cat)
        cl.save()
    verb_forms()
    init_quizzes()
    return HttpResponseRedirect(u'/quiz/')

def second_newest_categories (*args):
    smII = select_or_create(models.Category,
                           name=u'Spanish II Semester II Vocabulary'); smII.save()
    cat = select_or_create(models.Category,name=u'Lengua de las mariposas - I',parent=smII)
    cat.save()
    ifi = file(u'lengua1.txt',u'r')
    for l in ifi.readlines():
        words = l.split(':')
        words = [w.strip() for w in words]
        t = select_or_create(models.Triplet,l1=words[1],l2=words[0]); t.save()
        cl = models.CategoryLink(triplet=t,category=cat); cl.save()
        cl = models.CategoryLink(triplet=t,category=smII); cl.save()

def newest_categories (*args):
    return
    cat1 = select_or_create(models.Category,name=u'Spanish 4 Semester II Vocab'); cat.save()
    cat2 = select_or_create(models.Category,name=u'Immigration Vocab - Ramos - 1',parent=cat1); cat.save()
    qg = select_or_create(models.QuizGroup,name=u'Spanish IV')
    qgl = select_or_create(models.QuizGroupLink,category=cat1,quizgroup=qg); qgl.save()
    qgl = select_or_create(models.QuizGroupLink,category=cat2,quizgroup=qg); qgl.save()
    ifi = file(u'lengua1.txt',u'r')
    for l in ifi.readlines():
        words = l.split(':')
        words = [w.strip() for w in words]
        t = select_or_create(models.Triplet,l1=words[1],l2=words[0]); t.save()
        cl = models.CategoryLink(triplet=t,categoryf=cat2); cl.save()
        cl = models.CategoryLink(triplet=t,category=smII); cl.save()
    
    
def init_quizzes (*args):
    make_quiz(u'Spanish II - Semester II',
              [models.Category.objects.get(name=u'Antepresente'),
               models.Category.objects.get(name=u'Lengua de las mariposas - I'),
               ]
              )
    make_quiz(u'Spanish II - Semester I Review',
              [models.Category.objects.get(name=u'Spanish II Semester I Vocabulary'),
               models.Category.objects.get(name=u'Preterit Tense Verbs'),
               models.Category.objects.get(name=u'Imperfect Verbs'),
               models.Category.objects.get(name=u'Present Tense Verbs'),
               ])
    make_quiz(u'Spanish IV',
              [models.Category.objects.get(name=u'Past Subjunctive Verbs'),
               models.Category.objects.get(name=u'Conditional Verbs')
               ])
