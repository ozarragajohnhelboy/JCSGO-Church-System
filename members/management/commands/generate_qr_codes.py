from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate QR codes for all users who don\'t have one yet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate QR codes even for users who already have them',
        )
        parser.add_argument(
            '--church',
            type=str,
            help='Generate QR codes only for users from a specific church domain',
        )

    def handle(self, *args, **options):
        force = options['force']
        church_domain = options.get('church')
        
        # Build queryset
        users = User.objects.filter(is_active=True)
        
        if church_domain:
            users = users.filter(church__domain=church_domain)
        
        if not force:
            users = users.filter(qr_code_image__isnull=True)
        
        total_users = users.count()
        
        if total_users == 0:
            self.stdout.write(
                self.style.WARNING('No users found to process.')
            )
            return
        
        self.stdout.write(f'Processing {total_users} users...')
        
        success_count = 0
        error_count = 0
        
        with transaction.atomic():
            for user in users:
                try:
                    if force and user.qr_code_image:
                        # Delete existing QR code image
                        user.qr_code_image.delete(save=False)
                    
                    # Generate new QR code
                    user.generate_qr_code()
                    success_count += 1
                    
                    self.stdout.write(
                        f'✓ Generated QR code for {user.full_name} ({user.email})'
                    )
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to generate QR code for {user.full_name}: {str(e)}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Generated {success_count} QR codes successfully. '
                f'{error_count} errors occurred.'
            )
        )
