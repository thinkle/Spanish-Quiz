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
import stats

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

# Quiz stuff - basic questions and answers

#     Quiz stuff - url-exposed 

def mc_r (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return mc(request, category, reverse=True, rightanswer=rightanswer, lastanswer=lastanswer)

def open_response_r (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return open_response(request, category, reverse=True, rightanswer=rightanswer, lastanswer=lastanswer)

@login_required
def open_response (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return quiz_question(request, category, reverse=reverse, rightanswer=rightanswer, lastanswer=lastanswer,
                         question_type=models.OPEN_RESPONSE)

@login_required
def mc (request, category, reverse=False, rightanswer=None, lastanswer=None):
    return quiz_question(request, category,
                  reverse=reverse,rightanswer=rightanswer,lastanswer=lastanswer,
                  question_type=models.MULTIPLE_CHOICE)

def open_response_answer (request,**kwargs):
    if request.method=='POST':
        kwargs['question_type']=models.OPEN_RESPONSE
        return answer(request, **kwargs)
    else:
        return HttpResponseRedirect('/')

    
def mc_answer (request):
    if request.method=='POST':
        return answer(request, question_type=models.MULTIPLE_CHOICE)
    else:
        return HttpResponseRedirect('/')

def answer (request, question_type=models.MULTIPLE_CHOICE, seqid=None):
    print 'answer...',question_type
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
        print 'OPEN!'
        correct_answer = correct_answer.lower()
        try:
            correct_answer = re.sub(u'\s*\([^)]*\)\s*','',correct_answer)
            print 'Fixing up answer...'
            answer = re.sub(u'\s-*\([^)]*\)','',answer)
            print 'Fixing up answer...'            
            answer = re.sub(u'(he|she|it) ','he/she/it ',answer)
            print 'Fixing up answer...'
            answer = re.sub(u'you all','you guys',answer)
            print 'Fixing up answer...'
            answer = re.sub(u"y'all",'you guys',answer)  
            print 'Fixing up answer...'
            answer = fix_accents(answer)
        except UnicodeError:
            #print 'Unicode Schmoonicode'
            import traceback; traceback.print_exc()
            #print 'ignore away!'
        #print 'Answer changed to: ',answer
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
                #print 'Alternative answer!',triplet.l1,triplet.l2,'=>',
                triplet = alternative
                #print triplet.l1,triplet.l2
                correct_answer = answer
    else:
        print 'Not open!'
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
    params = {}
    if seqid:
        method = do_sequence
        params['seqid']=seqid
    else:
        if question_type == models.MULTIPLE_CHOICE:
            method = mc
        elif question_type == models.OPEN_RESPONSE:
            method = open_response
        else:
            raise "unknown question type %s"%question_type
        params['reverse']=reverse
        params['category']=category
    params['rightanswer']=models.Triplet.objects.get(id=target)
    params['lastanswer']=qd
    return method(request,**params)

#     Quiz stuff - guts and convenience functions

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
        dummylinks = dummylinks.exclude(triplet__l1=q_a.triplet.l1)
        dummylinks = dummylinks.exclude(triplet__l2=q_a.triplet.l2)        
        # Find similar...
        idx = 0
        seed = random.randint(0,3); start=1; end=2
        #print 'seed=',seed
        if seed > 0:
            if seed==start:
                similarlinks = dummylinks.filter(triplet__l2__startswith=q_a.triplet.l2[0])
            elif seed==end:
                similarlinks = dummylinks.filter(triplet__l2__endswith=q_a.triplet.l2[-1:])
            else:
                if len(q_a.triplet.l2) > 3:
                    similarlinks = dummylinks.filter(triplet__l2__contains=q_a.triplet.l2[3])
                else:
                    similarlinks = dummylinks.filter(triplet__l2__startswith=q_a.triplet.l2[0])
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
            #if seed==start:
            #    #print 'Filtered on ',q_a.triplet.l2[:idx-1],'idx=',idx-1,len(dummylinks)
            #elif seed==end:
            #    #print 'Filtered on ',q_a.triplet.l2[-idx:],'idx=',idx-1,len(dummylinks)
            #else:
            #    #print 'Filtered on contains',q_a.triplet.l2[3:(3+idx)],'idx=',idx-1,len(dummylinks)
        dummylinks = dummylinks.order_by('?')        
        all_answers = [o.triplet for o in dummylinks[0:3]] + [q_a.triplet]
        random.shuffle(all_answers)
        answer_rows = [[all_answers[0],all_answers[1]],[all_answers[2],all_answers[3]]]
        return q_a.triplet,answer_rows
    else:
        return q_a.triplet

def generate_quiz_question_params (request, category, reverse=False, rightanswer=None, lastanswer=None,
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
    statistics = stats.Stats(category,request.user,lastanswer)
    statistics.fetch_props(
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
        'stats':statistics,
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
        parameters['action'] = '/mc/answer/'
    elif question_type == models.OPEN_RESPONSE:
        q_a = generate_question(category,request.user,mc=False)
        parameters['target'] = q_a
        parameters['action'] = '/or/answer/'        
    return parameters


# Category listing code

class Node:
    def __init__ (self, obj):
        print 'Add object',obj
        self.object = obj
        self.branches = []

    def add_branch (self, b):
        print 'add branch',self.object,'->',b
        self.branches.append(b)

    def __unicode__ (self):
        return u'<NODE %s [%s]>'%(self.object,len(self.branches))



def index (request):
    cat_tree,quizzes = get_cat_tree()
    seq_tree = get_sequence_tree()
    return render_to_response('index.html',
                              {'sequences':seq_tree,
                               'quizzes':quizzes,
                               'cat_tree':cat_tree,
                               }
                              )
def get_cat_tree ():
    #print 'INDEX!'
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
    qquery = models.QuizGroup.objects.all()
    quizzes = []
    for qg in qquery:
        node = Node(qg)
        for qgl in models.QuizGroupLink.objects.filter(quizgroup=qg):
            node.add_branch(qgl.category)
        quizzes.append(node)
    #print 'CAT TREE:',cat_tree
    return cat_tree,quizzes



@login_required
def quiz_question (request, category, reverse=False, rightanswer=None, lastanswer=None,
                   question_type=models.MULTIPLE_CHOICE
                   ):
    params = generate_quiz_question_params(request,category,reverse,rightanswer,lastanswer,question_type)
    if question_type == models.MULTIPLE_CHOICE:
        return render_to_response(
            'simple_quiz.html',
            params
         )
    elif question_type == models.OPEN_RESPONSE:
        return render_to_response(
            'open_response.html',
            params
            )
    else:
        raise error("Unknown question type")

def fix_accents (s):
    print 'Accent fixer got: ',s
    for c1,c2 in [(u'~n',u'ñ'),
                   (u"'e",u'é'),
                   (u"'a",u'á'),
                   (u"'i",u'í'),
                   (u"'o",u'ó'),
                   (u"'u",u'ú'),
                   (u'"u',u'ü'),
                   ]:
        s = s.replace(c1,c2)
    print 'Accent fixer returned: ',s
    return s


# Sequence stuff

def get_sequence_tree ():

    def add_to_tree (seq, tree):
        branch = Node(seq)
        tree.add_branch(branch)
        print 'Appending branch',branch,'to tree',tree
        for s in models.Sequence.objects.filter(parent=seq):
            add_to_tree(s,branch)

    sequences = models.Sequence.objects.filter(parent=None)
    seq_tree = Node(None)
    for s in sequences:
        print 'Adding',s,s.name,s.id
        add_to_tree(s,seq_tree)

    return seq_tree

def sequence (request):
    seq_tree = get_sequence_tree()
    return render_to_response('sequence.html',
                              {'sequences':seq_tree})

class SequenceItemEvaluation:

    def __init__ (self, user, seqitem):
        self.user = user
        self.seqitem = seqitem
        print 'Gathering stats on',self.seqitem.reverse,self.seqitem.question_type
        answers = models.QuizData.objects.filter(user=user).filter(triplet__categorylink__category=self.seqitem.category,
                                                                   reverse=self.seqitem.reverse,
                                                                   question_type=self.seqitem.question_type,
                                                                   )
        self.nanswers = answers.count()
        correct = answers.filter(correct=True).count()
        
        if self.nanswers < self.seqitem.minimum_problems:
            self.completed = False
            self.comment = 'Not enough problems complete (you answered %s, you need %s)'%(
                self.nanswers,
                self.seqitem.minimum_problems
                )
        elif self.nanswers > self.seqitem.maximum_problems:
            self.completed = True
            self.comment = 'Enough is enough already (maxed out at %s)'%self.seqitem.maximum_problems 
        else:
            if self.nanswers:
                percentage = float(correct)/self.nanswers
            else:
                percentage = 0
            if percentage > self.seqitem.threshold:
                self.completed = True
                self.comment = "You exceeded the threshold! (%2.0f%%) (%s questions, %s needed)"%(
                    percentage*100,
                    self.nanswers,
                    self.seqitem.minimum_problems
                    )
            else:                    
                self.completed = False
                self.comment = "You need %2.0f%% correct (you have %2.0f%%)"%(
                    self.seqitem.threshold*100,
                    percentage*100,
                    )
                if (self.nanswers > 2 * self.seqitem.minimum_problems
                    or
                    self.nanswers < 0.5 * self.seqitem.maximum_problems):
                    # Start letting them 
                    last_x_answers = answers.order_by('-answer_time')[:self.seqitem.minimum_problems]
                    last_x_answers_right = sum([o.correct and 1 or 0 for o in last_x_answers])
                    percentage = float(last_x_answers_right)/self.seqitem.minimum_problems
                    if percentage > self.seqitem.threshold:
                        self.completed = True
                        self.comment = 'You got %2.0f%% of the last %s problems right.'%(percentage*100,
                                                                                         self.seqitem.minimum_problems)
        print 'Evaluated',
        print self.seqitem,
        print self.completed,
        print self.comment

@login_required
def do_sequence (request, seqid, rightanswer=None, lastanswer=None, **ignored_args):
    evals = []
    seq = models.Sequence(seqid)
    firstitem = models.SequenceItem.objects.get(sequence=seq,
                                                prev=None)
    sie = SequenceItemEvaluation(request.user,firstitem)
    evals.append(sie)
    completed = sie.completed
    while completed:
        try:
            nxt = models.SequenceItem.objects.get(sequence=seq,
                                                  prev=evals[-1].seqitem)
        except:
            print 'No next'
            break
        else:
            sie = SequenceItemEvaluation(request.user,nxt)
            evals.append(sie)
            completed = sie.completed
    if sie.completed:
        sie = random.choice(evals)
    params = generate_quiz_question_params(request,sie.seqitem.category, rightanswer=rightanswer,
                                           lastanswer=lastanswer,
                                           reverse=sie.seqitem.reverse,
                                           question_type=sie.seqitem.question_type,
                                           )
    evals.reverse()
    params['seq_history'] = evals
    if sie.seqitem.question_type==models.MULTIPLE_CHOICE:
        params['action'] = '/seq/answer/%s/'%seqid
        return render_to_response(
            'simple_quiz.html',
            params
            )
    else:
        params['action'] = '/seq/answer/%s/open'%seqid        
        return render_to_response(
            'open_response.html',
            params
            )
