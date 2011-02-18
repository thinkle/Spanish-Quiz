import models
from django_openid_auth.models import UserOpenID
from django.contrib.auth.models import User
import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

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
        one_hour_ago = today - datetime.timedelta(hours=1)
        return StatSetSet(
            self.get_overall().attempts.filter(
                answer_time__gt=one_hour_ago,
                answer_time__lte=today
                )
            )

    @propify
    def get_last_day (self):
        today = datetime.datetime.utcnow()
        one_day_ago = today - datetime.timedelta(days=1)
        return StatSetSet(
            self.get_overall().attempts.filter(
                answer_time__gt=str(one_day_ago),
                answer_time__lte=str(today)
                )
            )

    @propify
    def get_last_week (self):
        today = datetime.datetime.utcnow()
        one_week_ago = today - datetime.timedelta(days=7)
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

def all_stats (request, category=None):
    statistics = []
    #print 'Category=',category
    if category and not isinstance(category,models.Category):
        category = models.Category.objects.get(id=int(category))
    for user in User.objects.all():
        #print user,user.first_name
        if not category:
            try:
                category = models.QuizData.objects.filter(user=user)[0].triplet.category
            except:
                category = models.Category.objects.all()[0]
        s = Stats(category,user)
        s.fetch_props(
            'last_day.overall.ratio','last_day.open.ratio','last_day.overall.perc','last_day.open.perc',
            'last_hour.overall.ratio','last_hour.open.ratio','last_hour.overall.perc','last_hour.open.perc',
            'last_week.overall.ratio','last_week.open.ratio','last_week.overall.perc','last_week.open.perc',            
            'overall.overall.ratio','overall.open.ratio','overall.overall.perc','overall.open.perc',
            'category.overall.ratio','category.open.ratio','category.overall.perc','category.open.perc',
            )
        statistics.append(s)
    return render_to_response('stats.html',{'stats':statistics,
                                            'categories':models.Category.objects.all(),
                                            'by_user':True
                                            })

def user_stats (request, user):
    if user and not isinstance(user,User):
        user = User.objects.get(id=int(user))
    statistics = []
    for category in models.Category.objects.all():
        if models.QuizData.objects.filter(user=user,triplet__categorylink__category=category).count() > 0:
            s = Stats(category,user)
            s.fetch_props(
                'last_day.overall.ratio','last_day.open.ratio','last_day.overall.perc','last_day.open.perc',
                'last_hour.overall.ratio','last_hour.open.ratio','last_hour.overall.perc','last_hour.open.perc',
                'last_week.overall.ratio','last_week.open.ratio','last_week.overall.perc','last_week.open.perc',            
                'overall.overall.ratio','overall.open.ratio','overall.overall.perc','overall.open.perc',
                'category.overall.ratio','category.open.ratio','category.overall.perc','category.open.perc'
                )
            statistics.append(s)
        else:
            print 'No stats for ',category,user
    return render_to_response('stats.html',{'stats':statistics,
                                            'categories':None,
                                            'users':User.objects.all(),
                                            'by_user':False,
                                            'user':user,
                                            }
                              )
        
