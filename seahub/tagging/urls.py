from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('tagging.views',
    url('^change/$', 'change', name='change_tag'),
    url('^(?P<tid>\d+)/([^/]+)/$', 'tag_detail', name='tag_detail'),
    url('^search/', 'search', name='search_tag'),
)
