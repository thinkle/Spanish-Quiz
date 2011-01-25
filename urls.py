from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^quizlet/', include('quizlet.foo.urls')),
                       (r'^profile/$','quiz.views.profile'),
                       #(r'^logout/$','quiz.views.logout_user'),
                       (r'^logout/$','django.contrib.auth.views.logout', {'next_page':'/'}),
                       ('mc/(\d*)/$','quiz.views.mc'),
                       ('mc/(\d*)/r/$','quiz.views.mc_r'),                       
                       #('mc/right/(\d*)$','quiz.views.mc_right'),
                       #('mc/wrong/(\d*)$','quiz.views.mc_wrong'),
                       ('mc/answer/','quiz.views.mc_answer'),                       
                       ('quiz/','quiz.views.index'),
                       ('^$','quiz.views.index'),                       
                       ('init','quiz.quizmaker.init'),
                       (r'^openid/', include('django_openid_auth.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)


