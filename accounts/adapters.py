from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a social provider,
        but before the login is actually performed.
        """
        # If the user is new (no pk), we want to prevent immediate login
        if not sociallogin.is_existing:
            # We allow the user to be created, but we want to intercept the first login
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social user. 
        """
        user = super().save_user(request, sociallogin, form)
        # Mark that this user was just created via social login
        request.session['social_signup_complete'] = True
        return user

    def get_login_redirect_url(self, request):
        """
        If this is the first time the user is logging in via social account,
        we might want to force a redirect back to login.
        """
        if request.session.get('social_signup_complete'):
            # Clear the flag
            del request.session['social_signup_complete']
            
            # Since allauth already logged them in, we actually need to LOG THEM OUT 
            # if we want them to "manually login again" as requested.
            from django.contrib.auth import logout
            logout(request)
            
            messages.success(request, "Your Google account has been successfully registered! Please click the Google button again to log in.")
            return reverse('login')
            
        return super().get_login_redirect_url(request)
