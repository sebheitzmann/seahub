from django import forms
from django.utils.translation import ugettext_lazy as _

class ChangeTagForm(forms.Form):
    repo_id = forms.CharField(min_length=36, max_length=36, error_messages={
            'required': _('Repo id is required'),
            'min_length': _('Repo id is too short (require 36 characters)'),
            'max_length': _('Repo id is too long (require 36 characters)'),
            })
    path = forms.CharField(max_length=4096, error_messages={
            'required': _('Path is required'),
            'max_length': _('Path is too long'),
            })
    tags = forms.CharField(max_length=100, error_messages={
            'required': _('Tags are required'),
            'max_length': _('Tags are too long (maximun is 100 characters)'),
            })
    
