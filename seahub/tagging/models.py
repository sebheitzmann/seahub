from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext

from seahub.utils import calc_file_path_hash
from seahub.utils.slugify import slugify as default_slugify

class Tag(models.Model):
    name = models.CharField(verbose_name=_('Name'), max_length=100, db_index=True)
    slug = models.SlugField(verbose_name=_('Slug'), max_length=100)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __unicode__(self):
        return self.name

    def slugify(self, tag, i=None):
        slug = default_slugify(tag) or '-'
        if i is not None:
            slug += "_%d" % i
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.slugify(self.name)
            super(Tag, self).save(*args, **kwargs)

class TaggedItem(models.Model):
    tag = models.ForeignKey(Tag, related_name="%(app_label)s_%(class)s_items")
    repo_id = models.CharField(max_length=36, db_index=True)
    path = models.TextField()
    path_hash = models.CharField(max_length=12, db_index=True)

    class Meta:
        verbose_name = _("Tagged Item")
        verbose_name_plural = _("Tagged Items")

    def __unicode__(self):
        return ugettext("%(path)s tagged with %(tag)s") % {
            "path": self.path,
            "tag": self.tag,
        }

    def save(self, *args, **kwargs):
        if not self.path_hash:
            self.path_hash = calc_file_path_hash(self.path)

        return super(TaggedItem, self).save(*args, **kwargs)

class UserTags(models.Model):
    '''Tags used by a user'''
    user = models.CharField(max_length=255, db_index=True)
    tag = models.ForeignKey(Tag)

    class Meta:
        unique_together = ('user', 'tag')

class GroupTags(models.Model):
    '''Tags used by a Group'''
    group_id = models.IntegerField(db_index=True)
    tag = models.ForeignKey(Tag)

    class Meta:
        unique_together = ('group_id', 'tag')