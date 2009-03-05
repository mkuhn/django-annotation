from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    (r'^drugbank/', include('annotate.drugbank.urls')),
    (r'^nlp/', include('annotate.nlp.urls')),
    (r'^p450/', include('annotate.p450.urls')),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
)
