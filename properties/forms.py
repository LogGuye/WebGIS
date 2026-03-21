from django import forms
from django.contrib.gis.geos import Point

from .models import Property


class PropertyCreateForm(forms.ModelForm):
    lat = forms.FloatField(label="Vĩ độ")
    lng = forms.FloatField(label="Kinh độ")

    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "property_type",
            "listing_status",
            "price",
            "area",
            "address",
            "is_featured",
        ]
        labels = {
            "title": "Tiêu đề",
            "description": "Mô tả",
            "property_type": "Loại bất động sản",
            "listing_status": "Trạng thái",
            "price": "Giá bán",
            "area": "Diện tích (m²)",
            "address": "Địa chỉ",
            "is_featured": "Đánh dấu nổi bật",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-geo")
        self.fields["description"].widget = forms.Textarea(attrs={"class": "form-geo", "rows": 5, "placeholder": "Mô tả ngắn về bất động sản..."})
        self.fields["title"].widget.attrs.setdefault("placeholder", "Ví dụ: Nhà phố 2 mặt tiền tại Quận 7")
        self.fields["address"].widget.attrs.setdefault("placeholder", "Số nhà, đường, quận/huyện, thành phố")
        self.fields["price"].widget.attrs.setdefault("placeholder", "Ví dụ: 5500000000")
        self.fields["area"].widget.attrs.setdefault("placeholder", "Ví dụ: 85")
        self.fields["lat"].widget.attrs.setdefault("placeholder", "Ví dụ: 10.7769")
        self.fields["lng"].widget.attrs.setdefault("placeholder", "Ví dụ: 106.7009")

    def save(self, commit=True, agent=None):
        obj = super().save(commit=False)
        obj.location = Point(self.cleaned_data["lng"], self.cleaned_data["lat"], srid=4326)
        if agent is not None:
            obj.agent = agent
        if commit:
            obj.save()
            self.save_m2m()
        return obj
