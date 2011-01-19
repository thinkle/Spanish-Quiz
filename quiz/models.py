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
    
class CategoryLink (models.Model):
    triplet = models.ForeignKey(Triplet)
    category = models.ForeignKey(Category)

class QuizData (models.Model):
    user = models.ForeignKey(User)
    triplet = models.ForeignKey(Triplet)
    answer_time = models.DateTimeField('time of answer')
    correct = models.BooleanField()
    speed = models.IntegerField()




    
