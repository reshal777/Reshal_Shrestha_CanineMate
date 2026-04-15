from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Setup Google OAuth credentials for django-allauth'

    def handle(self, *args, **options):
        # Google OAuth credentials from environment variables
        import os
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR('Error: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in environment variables.'))
            return
        
        # Get or create the social app
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Google OAuth app created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Google OAuth app already exists, updating credentials...'))
            google_app.client_id = client_id
            google_app.secret = client_secret
            google_app.save()
            self.stdout.write(self.style.SUCCESS('✓ Google OAuth credentials updated'))
        
        # Associate with all sites
        sites = Site.objects.all()
        google_app.sites.set(sites)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Associated with {sites.count()} site(s)'))
        self.stdout.write(self.style.SUCCESS('\n✓ Google OAuth setup complete! You can now sign in with Google.'))
