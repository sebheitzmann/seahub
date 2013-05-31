# -*- coding: utf-8 -*-
import os
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from seaserv import check_permission, get_file_id_by_path, get_file_size, \
    list_personal_repos_by_owner, list_share_repos, get_group_repos_by_owner,\
    list_inner_pub_repos_by_owner, get_shared_groups_by_repo

from seahub.auth.decorators import login_required
from seahub.tagging.forms import ChangeTagForm
from seahub.tagging.models import Tag, TaggedItem, UserTags, GroupTags
from seahub.utils import get_dir_files_last_modified, get_user_repos, HAS_FILE_SEARCH, calc_file_path_hash

if HAS_FILE_SEARCH:
    from seahub_extra.search.utils import update_file_tags_index

try:
    from seahub.settings import CLOUD_MODE
except ImportError:
    CLOUD_MODE = False

# Get an instance of a logger
logger = logging.getLogger(__name__)

def update_file_tags(user, repo_id, path, tags):
    path_hash = calc_file_path_hash(path)

    new_tags = [ t.strip() for t in tags.split(',') if t.strip() ]

    old_tags = [ t.tag.name for t in TaggedItem.objects.filter(repo_id=repo_id, path_hash=path_hash) ]

    new_tag_set = set(new_tags)
    old_tag_set = set(old_tags)

    added_tags = new_tag_set - old_tag_set
    deleted_tags = old_tag_set - new_tag_set

    # add new tags, including update user/group tag list
    for tag_name in added_tags:
        tag = Tag.objects.get_or_create(name=tag_name)
        item = TaggedItem(repo_id=repo_id, path=path, tag=tag)
        item.save()

        UserTags.objects.get_or_create(user=user, tag=tag)

        for group in get_shared_groups_by_repo(repo_id):
            GroupTags.objects.get_or_create(group_id=group.id, tag=tag)

    # handle deleted tags
    TaggedItem.objects.filter(repo_id=repo_id,
                              path_hash=path_hash,
                              tag__name__in=deleted_tags).delete()

    # update file tags in search index
    if HAS_FILE_SEARCH:
        try:
            update_file_tags_index (repo_id, path, new_tags)
        except Exception, e:
            logger.exception('Failed to update_file_tags_index: %s, %s, %s',
                             repo_id, path, new_tags)
            raise

@login_required
@transaction.commit_manually
def change(request):
    if request.method != 'POST':
        raise Http404

    change_tag_form = ChangeTagForm(request.POST)

    success = False

    if change_tag_form.is_valid():
        tags = change_tag_form.cleaned_data['tags']
        repo_id = change_tag_form.cleaned_data['repo_id']
        path = change_tag_form.cleaned_data['path']
        user = request.user.username

        try:
            update_file_tags(user, repo_id, path, tags)
        except:
            messages.error(request, _(u'Internal Error'))
        else:
            messages.success(request, _('Tags have successfully been changed.'))
            success = True
    else:
        for k in change_tag_form.errors:
            messages.error(request, change_tag_form.errors[k])

    if success:
        transaction.commit()
    else:
        transaction.rollback()

    next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = settings.SITE_ROOT
    return HttpResponseRedirect(next)

@login_required
def user_tags(request):
    '''List all tags used by a user'''
    tags = UserTags.filter(user=request.user).values('tag')
    return render_to_response('tagging/user_tags.html', {
            'tags': tags,
            }, context_instance=RequestContext(request))

@login_required
def group_tags(request):
    '''List all tags used by a group'''
    tags = GroupTags.filter(user=request.user).values('tag')
    return render_to_response('tagging/group_tags.html', {
            'tags': tags,
            }, context_instance=RequestContext(request))

@login_required
def list_user_files_by_tags(request):
    '''List all files a user can access which has this tag '''
    pass

@login_required
def list_group_files_by_tags(request):
    '''List all files in a group which has this tag '''
    pass