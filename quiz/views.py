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

@login_required
def profile (request):
    if request.method == 'POST':
        uf = UserForm(request.POST,instance=request.user)
        if uf.is_valid():
            uf.save()
        else:
            return HttpResponseRedirect('/profile/')
        return HttpResponseRedirect('/')
    else:
        uf = UserForm(instance=request.user)
    return render_to_response('profile.html',{'uf':uf})

# Quiz stuff

def propify (f):
    def _ (self, *args, **kwargs):
        propname = f.__name__[4:]
        if hasattr(self,propname):
            return getattr(self,propname)
        else:
            setattr(self,propname,f(self,*args,**kwargs))
            return getattr(self,propname)
    return _

class StatSet (object):

    def __init__ (self, attempts):
        self.attempts = attempts

    @propify 
    def get_num_attempts (self): return self.attempts.count()

    @propify
    def get_correct (self): return self.attempts.filter(correct=True)
    
    @propify
    def get_num_correct (self): return self.get_correct().count()
    
    @propify
    def average_speed (self):
        speed = self.get_attempts().extra(select={'totspeed':'sum(speed)'})[0].totspeed
        return float(speed) / self.get_num_attempts()
    @propify
    def get_ratio (self):
        return '%i/%i'%(self.get_num_correct(),self.get_num_attempts())
    @propify
    def get_perc (self):
        try:
            return '%i%%'%(100*float(self.get_num_correct())/self.get_num_attempts())
        except ZeroDivisionError:
            return '0'

class Stats (object):
    def __init__ (self, cat, user=None, lastanswer=None):
        self.cat = cat
        self.user = user
        self.lastanswer = lastanswer

    @propify
    def get_overall (self):
        return StatSet(models.QuizData.objects.filter(user=self.user))

    @propify
    def get_category (self):
        return StatSet(
            self.get_overall().attempts.filter(
                triplet__categorylink__category=self.cat
                )
            )

    @propify
    def get_last_hour (self):
        today = datetime.datetime.utcnow()
        one_hour_ago = today.replace(hour=today.hour - 1)
        return StatSet(
            self.get_overall().attempts.filter(
                answer_time__gt=one_hour_ago,
                answer_time__lte=today
                )
            )

    @propify
    def get_last_day (self):
        today = datetime.datetime.utcnow()
        one_hour_ago = today.replace(day=today.day - 1)
        return StatSet(
            self.get_overall().attempts.filter(
                answer_time__gt=str(one_hour_ago),
                answer_time__lte=str(today)
                )
            )

    @propify
    def get_last_week (self):
        today = datetime.datetime.utcnow()
        one_week_ago = today.replace(day=today.day-7)
        return StatSet(
            self.get_overall().attempts.filter(
                answer_time__gt=str(one_week_ago),
                answer_time__lt=str(today),
                )
            )

    @propify
    def get_previous_attempts (self):
        if not self.lastanswer: return None
        attempts = self.get_overall().attempts.filter(triplet=self.lastanswer.triplet)
        if attempts.count() > 1:
            attempts = attempts.order_by('answer_time')
            attmps = []
            for a in attempts:
                attmps.append(a)
            return attmps[:-1]
        else:
            return None

    @propify
    def get_previous_attempt_history (self):
        if not self.lastanswer: return None
        try:
            retval = [
                a.correct and 'Right' or 'Wrong'
                for a in self.get_previous_attempts()
                ]
        except:
            return ''
        else:
            return ' '.join(retval)

    def fetch_props (self, *props):
        for p in props:
            if '.' in p:
                slf = self
                for subp in p.split('.'):
                    getattr(slf,'get_'+subp)()
                    slf = getattr(slf,subp)
            else:
                getattr(self,'get_'+p)()
        
def filter_questions (catlinks, user, min_questions = 4):
    # Never allow last question...
    try:
        last_question = models.QuizData.objects.filter(user=user).order_by('-answer_time')[0]
    except IndexError:
        pass
    else:
        catlinks = catlinks.exclude(triplet=last_question.triplet)
    previous_right = models.QuizData.objects.filter(user=user).filter(correct=True).order_by('-answer_time')
    previous_wrong = models.QuizData.objects.filter(user=user).filter(correct=False).order_by('-answer_time')
    # Remove previous items...
    idx = 0; num_prev_right = previous_right.count()
    num_possible = catlinks.count()
    max_to_exclude = num_possible - min_questions
    to_exclude = previous_right[0:max_to_exclude]
    catlinks = catlinks.exclude(
        triplet__in=[qd.triplet for qd in to_exclude]
        )
    return catlinks

def pick_question (catlinks, user):
    ## Given a narrowed field of questions, pick one
    catlinks = catlinks.order_by('?')
    q_a = catlinks[0]
    return q_a

def generate_question (cat, user=None):
    q_a = None
    orig_catlinks = catlinks = models.CategoryLink.objects.filter(category=cat)
    too_many_right = 3
    # Apply filters...
    assert(catlinks.count() > 3)
    # Filter catlinks
    catlinks = filter_questions(catlinks, user)
    q_a = pick_question(catlinks, user)
    # Very lame attempt to make choices harder (more similar to each other)
    #my_similar_links = filter(lambda x: x.triplet.l2.startswith(q_a.l2[0]), my_links)
    #if len(my_similar_links) >= 3:
    #    my_links = my_similar_links
    dummylinks = orig_catlinks.exclude(id=q_a.id)
    all_answers = [o.triplet for o in dummylinks[0:3]] + [q_a.triplet]
    random.shuffle(all_answers)
    answer_rows = [[all_answers[0],all_answers[1]],[all_answers[2],all_answers[3]]]
    return q_a.triplet,answer_rows

def index (request):
    cats = models.Category.objects.all()
    return render_to_response(
        'index.html',
        {'data':cats})

def mc_r (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return mc(request, category, reverse=True, rightanswer=rightanswer, lastanswer=lastanswer)

@login_required
def mc (request, category, reverse=False, rightanswer=None, lastanswer=None):
    category = int(category)
    cat = models.Category.objects.get(id=category)
    try:
        uoid = UserOpenID.objects.get(user=request.user)
    except:
        class o:
            pass
        uoid = o()
        uoid.display_id = 'None'
        uoid.claimed_id=None
    stats = Stats(cat,request.user,lastanswer)
    stats.fetch_props(
        #'cat_attempts','num_cat_attempts',
        'category.ratio','category.perc','overall.ratio','overall.perc',
        'last_hour.ratio','last_hour.perc','last_day.ratio','last_day.perc',
        'last_week.ratio','last_week.perc',        
        'previous_attempts','previous_attempt_history')
    q_a,answer_rows = generate_question(cat,request.user)
    return render_to_response(
        'simple_quiz.html',
        {'stats':stats,
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

def all_stats (request, category=None):
    stats = []
    for user in User.objects.all():
        print user,user.first_name
        if not category:
            try:
                category = models.QuizData.objects.filter(user=user)[0].triplet.category
            except:
                category = models.Category.objects.all()[0]
        s = Stats(category,user)
        s.fetch_props(
            'last_day.ratio','last_day.perc',
            'last_hour.ratio','last_hour.perc',
            'last_week.ratio','last_week.perc',            
            'overall.ratio','overall.perc',
            'category.ratio','category.perc'
            )
        stats.append(s)
    print 'stats=',stats
    return render_to_response('stats.html',{'stats':stats})

        

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



                

