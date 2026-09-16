import json

from django import forms


class JSONRPCCallForm(forms.Form):
    """A method name and its params, entered as a JSON object."""

    method = forms.CharField(
        label="Метод", 
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "например, auth.check"}),
    )
    params = forms.CharField(
        label="Параметры (JSON объект)",
        required=False,
        initial="{}",
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": '{"key": "value"}'}),
    )

    def clean_params(self) -> dict:
        raw = self.cleaned_data.get("params", "{}").strip() or "{}"
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Неверный JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise forms.ValidationError("Параметры должны быть JSON объектом, например {}")
        return value