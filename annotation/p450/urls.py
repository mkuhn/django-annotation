from django.conf.urls.defaults import *
from annotate.p450.models import *

cand_dict = {
    'queryset': Candidate.objects.all(),
}

urlpatterns = patterns('',
    (r'^candidates/$',                               'django.views.generic.list_detail.object_list', cand_dict),
    (r'^candidates/(?P<object_id>-?\d+)/$',            'annotate.p450.views.candidate',),
    (r'^candidates/export/$',            'annotate.p450.views.candidate_export',),
)

