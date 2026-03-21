from django import forms

from properties.models import Property
from .models import Appointment, Lead


class AppointmentCreateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["lead", "property", "scheduled_at", "notes"]
        labels = {
            "lead": "Khách hàng",
            "property": "Bất động sản",
            "scheduled_at": "Thời gian hẹn",
            "notes": "Ghi chú",
        }
        widgets = {
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-geo"}),
            "notes": forms.Textarea(attrs={"class": "form-geo", "rows": 4, "placeholder": "Ghi chú cho buổi hẹn xem nhà..."}),
        }

    def __init__(self, *args, **kwargs):
        role = kwargs.pop("role", None)
        linked_agent = kwargs.pop("linked_agent", None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-geo")
        if role == "agent" and linked_agent:
            self.fields["lead"].queryset = Lead.objects.filter(assigned_agent=linked_agent)
            self.fields["property"].queryset = Property.objects.filter(agent=linked_agent)
        else:
            self.fields["lead"].queryset = Lead.objects.all()
            self.fields["property"].queryset = Property.objects.all()
