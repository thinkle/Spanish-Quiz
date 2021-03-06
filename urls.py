from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^quizlet/', include('quizlet.foo.urls')),
                       (r'^all/$','quiz.views.show_all'),
                       (r'^profile/$','quiz.views.profile'),
                       (r'^stats/$','quiz.stats.all_stats'),
                       (r'^stats/category/(\d+)$/?','quiz.stats.all_stats'),
                       (r'^stats/user/(\d+)$/?','quiz.stats.user_stats'),
                       #(r'^logout/$','quiz.views.logout_user'),
                       (r'^logout/$','django.contrib.auth.views.logout', {'next_page':'/'}),
                       ('^mc/(\d*)/$','quiz.views.mc'),
                       ('^mc/(\d*)/r/$','quiz.views.mc_r'),
                       ('^or/(\d*)/$','quiz.views.open_response'),
                       ('^or/(\d*)/r$','quiz.views.open_response_r'),                       
                       ('^or/answer/$','quiz.views.open_response_answer'),                       
                       #('mc/right/(\d*)$','quiz.views.mc_right'),
                       #('mc/wrong/(\d*)$','quiz.views.mc_wrong'),
                       ('^mc/answer/','quiz.views.mc_answer'),                       
                       ('^quiz/$','quiz.views.index'),
                       ('^$','quiz.views.index'),                       
                       #('^init$','quiz.quizmaker.init'),
                       ('clean','quiz.quizmaker.cleanup_old_mistakes'),
                       ('init_newest','quiz.quizmaker.newest_categories'),
                       ('init_quizzes','quiz.quizmaker.init_quizzes'),
                       ('init_quizzes','quiz.quizmaker.init_quizzes'),
                       (r'^openid/', include('django_openid_auth.urls')),
                       (r'^new/category/$','quiz.quizuploader.new_category'),
                       (r'^new/triplets/$','quiz.quizuploader.new_triplets'),
                       (r'^new/qg/$','quiz.quizuploader.new_quizgrouplink'),
                       (r'^new/$','quiz.quizuploader.uploader'),
                       (r'^new/sequence/$','quiz.quizuploader.new_sequence'),
                       (r'^new/sequenceitem/$','quiz.quizuploader.new_sequenceitem'),
                       (r'^new/append_seq/','quiz.quizuploader.append_sequence_items'),
                       (r'^seq/$','quiz.views.sequence'),
                       (r'^seq/(\d+)/','quiz.views.do_sequence'),
                       (r'^seq/answer/(?P<seqid>\d+)/$','quiz.views.answer'),
                       (r'^seq/answer/(?P<seqid>\d+)/open','quiz.views.open_response_answer'),                       



    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)


