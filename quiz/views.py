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

# User stuff

class UserForm (ModelForm):
    class Meta:
        model = User
        fields = ["first_name","last_name","email"]

def logout_user (request):
    logout(request)
    return HttpResponseRedirect('/')

def show_all (request):
    cl = models.CategoryLink.objects.all().order_by("triplet__l2")
    return render_to_response('all.html',{'links':cl})

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

class StatSetSet (object):

    def __init__ (self, attempts):
        self.attempts = attempts

    @propify 
    def get_open (self):
        return StatSet(self.attempts.filter(
            question_type=models.OPEN_RESPONSE
            )
                       )

    @propify
    def get_mc (self):
        return StatSet(self.attempts.filter(
            question_type=models.MULTIPLE_CHOICE
            )
                       )

    @propify
    def get_overall (self):
        return StatSet(self.attempts)

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
    def get_num_correct_open (self): return self.get_correct().count()

    @propify
    def get_num_correct_mc (self): return self.get_correct().count()

    
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
        return StatSetSet(models.QuizData.objects.filter(user=self.user))

    @propify
    def get_category (self):
        return StatSetSet(
            self.get_overall().attempts.filter(
                triplet__categorylink__category=self.cat
                )
            )

    @propify
    def get_last_hour (self):
        today = datetime.datetime.utcnow()
        one_hour_ago = today.replace(hour=today.hour - 1)
        return StatSetSet(
            self.get_overall().attempts.filter(
                answer_time__gt=one_hour_ago,
                answer_time__lte=today
                )
            )

    @propify
    def get_last_day (self):
        today = datetime.datetime.utcnow()
        one_hour_ago = today.replace(day=today.day - 1)
        return StatSetSet(
            self.get_overall().attempts.filter(
                answer_time__gt=str(one_hour_ago),
                answer_time__lte=str(today)
                )
            )

    @propify
    def get_last_week (self):
        today = datetime.datetime.utcnow()
        one_week_ago = today.replace(day=today.day-7)
        return StatSetSet(
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
    catlinks = catlinks.order_by('?')
    return catlinks

def pick_question (catlinks, user):
    ## Given a narrowed field of questions, pick one
    catlinks = catlinks.order_by('?')
    q_a = catlinks[0]
    return q_a

def generate_question (cat, user=None, mc=True):
    q_a = None
    orig_catlinks = catlinks = models.CategoryLink.objects.filter(category=cat)
    too_many_right = 3
    # Apply filters...
    assert(catlinks.count() > 3)
    # Filter catlinks
    catlinks = filter_questions(catlinks, user)
    q_a = pick_question(catlinks, user)
    if mc:
        # Very lame attempt to make choices harder (more similar to each other)
        #my_similar_links = filter(lambda x: x.triplet.l2.startswith(q_a.l2[0]), my_links)
        #if len(my_similar_links) >= 3:
        #    my_links = my_similar_links
        dummylinks = orig_catlinks.exclude(id=q_a.id)
        dummylinks = orig_catlinks.exclude(triplet__l1=q_a.triplet.l1)
        dummylinks = orig_catlinks.exclude(triplet__l2=q_a.triplet.l2)        
        # Find similar...
        idx = 0
        seed = random.randint(0,3); start=1; end=2
        print 'seed=',seed
        if seed > 0:
            if seed==start:
                similarlinks = dummylinks.filter(triplet__l2__startswith=q_a.triplet.l2[0])
            elif seed==end:
                similarlinks = dummylinks.filter(triplet__l2__endswith=q_a.triplet.l2[-1:])
            else:
                similarlinks = dummylinks.filter(triplet__l2__contains=q_a.triplet.l2[3])
            while len(similarlinks) > 3:
                dummylinks = similarlinks
                idx += 1
                if idx > 4: break
                if seed==start:
                    similarlinks = dummylinks.filter(
                        triplet__l2__startswith=q_a.triplet.l2[0:idx]
                        )
                elif seed==end:
                    similarlinks = dummylinks.filter(
                        triplet__l2__endswith=q_a.triplet.l2[-(idx+1):]
                        )
                else:
                    similarlinks = dummylinks.filter(
                        triplet__l2__contains=q_a.triplet.l2[3:(3+idx)]
                        )
            if seed==start:
                print 'Filtered on ',q_a.triplet.l2[:idx-1],'idx=',idx-1,len(dummylinks)
            elif seed==end:
                print 'Filtered on ',q_a.triplet.l2[-idx:],'idx=',idx-1,len(dummylinks)
            else:
                print 'Filtered on contains',q_a.triplet.l2[3:(3+idx)],'idx=',idx-1,len(dummylinks)
        dummylinks = dummylinks.order_by('?')        
        all_answers = [o.triplet for o in dummylinks[0:3]] + [q_a.triplet]
        random.shuffle(all_answers)
        answer_rows = [[all_answers[0],all_answers[1]],[all_answers[2],all_answers[3]]]
        return q_a.triplet,answer_rows
    else:
        return q_a.triplet

class Node:
    def __init__ (self, obj):
        self.object = obj
        self.branches = []

    def add_branch (self, b):
        self.branches.append(b)

def index (request):
    print 'INDEX!'
    top_cats = models.Category.objects.filter(parent=None)
    cat_tree = Node(None)
    def add_to_tree (category, tree):
        branch = Node(category)
        tree.add_branch(branch)
        for c in models.Category.objects.filter(parent=category):
            if models.CategoryLink.objects.filter(category=c):
                add_to_tree(c,branch)
    for c in top_cats:
        add_to_tree(c,cat_tree)
    print 'CAT TREE:',cat_tree
    qquery = models.QuizGroup.objects.all()
    quizzes = []
    for qg in qquery:
        node = Node(qg)
        for qgl in models.QuizGroupLink.objects.filter(quizgroup=qg):
            node.add_branch(qgl.category)
        quizzes.append(node)
    return render_to_response(
        'index.html',
        {'cat_tree':cat_tree,
         'quizzes':quizzes,
         })

def mc_r (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return mc(request, category, reverse=True, rightanswer=rightanswer, lastanswer=lastanswer)

def open_response_r (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return open_response(request, category, reverse=True, rightanswer=rightanswer, lastanswer=lastanswer)

def quiz_question (request, category, reverse=False, rightanswer=None, lastanswer=None,
                   question_type=models.MULTIPLE_CHOICE):
    if not isinstance(category,models.Category):
        category = int(category)
        category = models.Category.objects.get(id=category)
    try:
        uoid = UserOpenID.objects.get(user=request.user)
    except:
        class o:
            pass
        uoid = o()
        uoid.display_id = 'None'
        uoid.claimed_id=None
    stats = Stats(category,request.user,lastanswer)
    stats.fetch_props(
        #'category_attempts','num_category_attempts',
        'category.overall.ratio','category.mc.ratio','category.open.ratio',
        'category.mc.perc','category.open.perc',
        'category.overall.perc','overall.overall.ratio','overall.overall.perc',
        'overall.open.perc',
        'last_hour.overall.ratio','last_hour.overall.perc','last_day.overall.ratio',
        'last_day.overall.perc','last_hour.open.perc','last_day.open.perc','last_week.open.perc',
        'last_week.overall.ratio','last_week.overall.perc',       
        'previous_attempts','previous_attempt_history')
    parameters = {
        'stats':stats,
        'category':category,
        'reverse':reverse,
        'rightanswer':rightanswer,
        'time':time.time(),
        'lastanswer':lastanswer,
        'user':request.user,
        'uoid':uoid.display_id,
        }
    if question_type == models.MULTIPLE_CHOICE:
        q_a,answer_rows = generate_question(category,request.user)
        parameters['answer_rows'] = answer_rows
        parameters['target'] = q_a
        return render_to_response(
            'simple_quiz.html',
            parameters
         )
    elif question_type == models.OPEN_RESPONSE:
        q_a = generate_question(category,request.user,mc=False)
        parameters['target'] = q_a
        return render_to_response(
            'open_response.html',
            parameters
            )
    else:
        raise error("Unknown question type")

def open_response (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return quiz_question(request, category, reverse=reverse, rightanswer=rightanswer, lastanswer=lastanswer,
                         question_type=models.OPEN_RESPONSE)

@login_required
def mc (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return quiz_question(request, category,
                  reverse=reverse,rightanswer=rightanswer,lastanswer=lastanswer,
                  question_type=models.MULTIPLE_CHOICE)

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

def answer (request, question_type=models.MULTIPLE_CHOICE):
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
    triplet=models.Triplet.objects.get(id=target)
    if reverse=='False': reverse = False
    else: reverse = True
    if question_type == models.OPEN_RESPONSE:
        correct_answer = correct_answer.lower()
        correct_answer = re.sub('\s-*\([^)]*\)','',correct_answer)
        answer = re.sub('\s-*\([^)]*\)','',answer)
        answer = re.sub('(he|she|it) ','he/she/it ',answer)
        answer = re.sub('you all','you guys',answer)
        answer = re.sub("y'all",'you guys',answer)                
        answer = fix_accents(answer)
        print 'Answer changed to: ',answer
        if answer != correct_answer:
            # Check if there's another answer out there...
            try:
                if triplet.l1 == correct_answer:
                    alternative = models.Triplet.objects.get(l1=answer,l2=triplet.l2)
                else:
                    alternative = models.Triplet.objects.get(l1=triplet.l1,l2=answer)
            except:
                pass
            else:
                print 'Alternative answer!',triplet.l1,triplet.l2,'=>',
                triplet = alternative
                print triplet.l1,triplet.l2
                correct_answer = answer
    try:
        qd = models.QuizData(
            user=request.user,
            triplet=triplet,
            reverse=reverse,
            question_type=question_type,
            correct=(answer.lower()==correct_answer.lower()),
            speed=speed,
            answer_time=datetime.datetime.today(),
            )
    except:
        qd = models.QuizData(
            triplet=triplet,
            reverse=reverse,
            question_type=question_type,
            correct=(answer.lower()==correct_answer.lower()),
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
    if question_type == models.MULTIPLE_CHOICE:
        method = mc
    elif question_type == models.OPEN_RESPONSE:
        method = open_response
    else:
        raise error("unknown question type %s"%question_type)
    return method(request,category=category,reverse=reverse,rightanswer=models.Triplet.objects.get(id=target),
                  lastanswer=qd)

def fix_accents (s):
    for c1,c2 in [('~n',u'ñ'),
                   ("'e",u'é'),
                   ("'a",u'á'),
                   ("'i",u'í'),
                   ("'o",u'ó'),
                   ("'u",u'ú'),
                   ('"u',u'ü'),
                   ]:
        s = s.replace(c1,c2)
    return s

def open_response_answer (request):
    if request.method=='POST':
        return answer(request, question_type=models.OPEN_RESPONSE)
    else:
        return HttpResponseRedirect('/')
    
def mc_answer (request):
    if request.method=='POST':
        return answer(request, question_type=models.MULTIPLE_CHOICE)
    else:
        return HttpResponseRedirect('/')



                

