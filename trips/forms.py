from django import forms
from network.models import Node


class CreateTripForm(forms.Form):
    start_node = forms.ModelChoiceField(
        queryset=Node.objects.all(),
        label='Starting Location',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    end_node = forms.ModelChoiceField(
        queryset=Node.objects.all(),
        label='Destination',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    max_passengers = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=3,
        label='Max Passengers',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_node')
        end = cleaned_data.get('end_node')
        if start and end and start == end:
            raise forms.ValidationError('Start and end must be different.')
        return cleaned_data
