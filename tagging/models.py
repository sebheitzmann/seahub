from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext

from seahub.utils import calc_file_path_hash
from seahub.utils.slugify import slugify as default_slugify

class TagManager(models.Manager):
    def add(self, *tags, **kwargs):
        tag_objs = set()
        str_tags = set(tags)
        existing = self.model.objects.filter(name__in=str_tags)
        tag_objs.update(existing)

        for new_tag in str_tags - set(t.name for t in existing):
            if not new_tag:
                continue
            tag_objs.add(self.model.objects.create(name=new_tag))

        for tag in tag_objs:
            TaggedItem.objects.get_or_create(tag=tag, **kwargs)

        tags_for_removal = [ e.name for e in self.all(**kwargs) \
                                 if e.name not in str_tags]
        self.remove(*tags_for_removal, **kwargs)

    def remove(self, *tags, **kwargs):
        if kwargs.get('repo_id', '') and kwargs.get('path', ''):
            TaggedItem.objects.filter(**kwargs).filter(tag__name__in=tags).delete()
        else:
            TaggedItem.objects.filter(**{'user':kwargs.get(
                        'user', '')}).filter(tag__name__in=tags).delete()

    def all(self, **kwargs):
        if kwargs.get('repo_id', '') and kwargs.get('path', ''):
            path_hash = calc_file_path_hash(kwargs.get('path'))
            tag_ids = TaggedItem.objects.filter(**{
                    'repo_id': kwargs.get('repo_id'),
                    'path_hash': path_hash}).values('tag_id').distinct()
            return Tag.objects.filter(id__in=tag_ids)
        else:
            tag_ids = TaggedItem.objects.filter(**{
                    'user': kwargs.get('user', '')}).values('tag_id').distinct()
            return Tag.objects.filter(id__in=tag_ids)
            
class Tag(models.Model):
    """

    # List tags of a user.
    >>> Tag.objects.all(user='foo@foo.com')
    []
    
    # Create one tag for a file.
    >>> Tag.objects.add('foo', **{'repo_id':'123', 'path':'/test.c', 'user':'foo@foo.com'})
    >>> Tag.objects.all(user='foo@foo.com')
    [<Tag: foo>]
    >>> TaggedItem.objects.all()
    [<TaggedItem: /test.c tagged with foo>]

    # Create another tag for the file.
    >>> Tag.objects.add('foo', 'bar', **{'repo_id':'123', 'path':'/test.c', 'user':'foo@foo.com'})
    >>> Tag.objects.all(user='foo@foo.com')
    [<Tag: foo>, <Tag: bar>]
    >>> TaggedItem.objects.all()
    [<TaggedItem: /test.c tagged with foo>, <TaggedItem: /test.c tagged with bar>]

    # Remove one tag and add another one.
    >>> Tag.objects.add('foo', 'baz', **{'repo_id':'123', 'path':'/test.c', 'user':'foo@foo.com'})
    >>> Tag.objects.all(user='foo@foo.com')
    [<Tag: foo>, <Tag: baz>]
    >>> TaggedItem.objects.all()
    [<TaggedItem: /test.c tagged with foo>, <TaggedItem: /test.c tagged with baz>]

    # Now list tags of the user again.
    >>> Tag.objects.all(user='foo@foo.com')
    [<Tag: foo>, <Tag: baz>]

    """
    name = models.CharField(verbose_name=_('Name'), max_length=100, db_index=True)
    slug = models.SlugField(verbose_name=_('Slug'), max_length=100)
    objects = TagManager()

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
    user = models.CharField(verbose_name=('Email'), max_length=255,
                            db_index=True)

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
