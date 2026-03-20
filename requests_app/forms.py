from django import forms
from network.models import Node


class CarpoolRequestForm(forms.Form):
    pickup_node = forms.ModelChoiceField(
        queryset=Node.objects.all(),
        label='Your Pickup Location',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    dropoff_node = forms.ModelChoiceField(
        queryset=Node.objects.all(),
        label='Your Destination',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        pickup = cleaned_data.get('pickup_node')
        dropoff = cleaned_data.get('dropoff_node')
        if pickup and dropoff and pickup == dropoff:
            raise forms.ValidationError('Pickup and dropoff must be different.')
        return cleaned_data
