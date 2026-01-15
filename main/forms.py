
import random
import string
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import ProfilMembre

class InscriptionForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    numero_etudiant = forms.CharField(max_length=20, required=True)
    telephone = forms.CharField(max_length=20, required=True)
    niveau_academique = forms.ChoiceField(choices=ProfilMembre.NIVEAU_CHOICES, required=True)
    specialisation = forms.ChoiceField(choices=ProfilMembre.SPECIALISATION_CHOICES, required=True)
    newsletter_acceptee = forms.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte avec cette adresse email existe déjà.")
        return email
    
    def clean_numero_etudiant(self):
        numero_etudiant = self.cleaned_data.get('numero_etudiant')
        if ProfilMembre.objects.filter(numero_etudiant=numero_etudiant).exists():
            raise forms.ValidationError("Ce numéro étudiant est déjà utilisé.")
        return numero_etudiant
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Générer un username unique
        email = self.cleaned_data['email']
        base_username = email.split('@')[0]
        import re
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username)
        
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        user.username = username
        
        if commit:
            user.save()
        return user


class ConnexionForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    remember_me = forms.BooleanField(required=False)
