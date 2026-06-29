from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        help_text=""
    )

    email = forms.EmailField(
        required=True,
        error_messages={'required': "L'adresse email est obligatoire."}
    )

    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        required=True,
        error_messages={'required': "Veuillez indiquer votre sexe."}
    )

    birth_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Nom d'utilisateur"
        self.fields['password1'].help_text = ""
        self.fields['password2'].help_text = ""
        self.fields['photo'].label = "Photo de profil (optionnel)"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'gender',
            'role',
            'photo',
            'bio',
            'birth_date',
            'password1',
            'password2',
        )
