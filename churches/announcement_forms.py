from django import forms
from django.utils import timezone

from churches.models import ChurchAnnouncement


class ChurchAnnouncementForm(forms.ModelForm):
    class Meta:
        model = ChurchAnnouncement
        fields = ('title', 'content', 'priority', 'start_date', 'end_date', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'end_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']
        self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']
        self.fields['end_date'].required = False
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.localtime(timezone.now()).strftime(
                '%Y-%m-%dT%H:%M'
            )
            self.fields['is_active'].initial = True
        else:
            if self.instance.start_date:
                self.initial['start_date'] = timezone.localtime(
                    self.instance.start_date
                ).strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_date:
                self.initial['end_date'] = timezone.localtime(
                    self.instance.end_date
                ).strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned = super().clean()
        start_date = cleaned.get('start_date')
        end_date = cleaned.get('end_date')
        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', 'End date must be after the start date.')
        return cleaned
