from django import forms

from .models import PropertyImage


class PropertyImageUploadForm(forms.Form):
    images = forms.FileField(
        label="Ảnh bất động sản",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-geo"}),
    )


class PropertyImageOrderForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ["sort_order"]
        widgets = {
            "sort_order": forms.NumberInput(attrs={"class": "form-geo", "min": 0, "style": "max-width:96px"}),
        }
