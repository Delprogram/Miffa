from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        help_text=""  # 👈 enlève le texte d’aide
    )

    birth_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # supprimer les textes d’aide
        self.fields['username'].help_text = "Nom d'utilisateur"
        self.fields['password1'].help_text = ""
        self.fields['password2'].help_text = ""
        self.fields['photo'].label = "Photo de profil (optionnel)"


    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'role',
            'photo',
            'bio',
            'birth_date',
            'password1',
            'password2',
        )