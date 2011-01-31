from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Triplet (models.Model):
    
    l1 = models.CharField(max_length=250)
    l2 = models.CharField(max_length=250)
    notes = models.TextField()

class Category (models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    parent = models.ForeignKey('self',null=True)

    def children (self):
        return Category.objects.filter(parent=self)

    def __repr__ (self):
        if self.parent:
            return '<Category %s:%s >'%(self.parent.name,self.name)
        else:
            return '<Category %s >'%self.name
        
class CategoryLink (models.Model):
    triplet = models.ForeignKey(Triplet)
    category = models.ForeignKey(Category)

    def save (self, *args, **kwargs):
        retval = models.Model.save(self,*args,**kwargs)
        if self.category.parent is not None:
            if self.category.parent is not None:
                cl = CategoryLink(triplet=self.triplet,category=self.category.parent)
                cl.save()
            else:
                print 'WTF?!?'
        return retval


MULTIPLE_CHOICE = 0
OPEN_RESPONSE = 1

class QuizGroup (models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    parent = models.ForeignKey('self',null=True)

class QuizGroupLink (models.Model):
    category = models.ForeignKey(Category)
    quizgroup = models.ForeignKey(QuizGroup)    

class QuizData (models.Model):
    user = models.ForeignKey(User,null=True)
    triplet = models.ForeignKey(Triplet)
    reverse = models.BooleanField()
    question_type = models.IntegerField()
    answer_time = models.DateTimeField('time of answer')
    correct = models.BooleanField()
    speed = models.IntegerField()


