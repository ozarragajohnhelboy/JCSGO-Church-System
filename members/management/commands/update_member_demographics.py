from django.core.management.base import BaseCommand
from django.db import transaction, models
from members.models import CustomUser
from datetime import date
import random


class Command(BaseCommand):
    help = 'Update existing members with missing demographic data (birth_date and gender)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--auto-fill',
            action='store_true',
            help='Automatically fill missing data with random values for testing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_fill = options['auto_fill']
        
        # Find members with missing demographic data
        members_without_data = CustomUser.objects.filter(
            is_active=True,
            is_new_friend=False
        ).filter(
            models.Q(birth_date__isnull=True) | models.Q(gender__isnull=True) | models.Q(gender='')
        )
        
        count = members_without_data.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All regular members have complete demographic data!')
            )
            return
        
        self.stdout.write(f'Found {count} members with incomplete demographic data:')
        self.stdout.write('')
        
        for member in members_without_data:
            missing_fields = []
            if not member.birth_date:
                missing_fields.append('birth_date')
            if not member.gender:
                missing_fields.append('gender')
            
            self.stdout.write(f'  - {member.full_name} ({member.email}): Missing {", ".join(missing_fields)}')
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('DRY RUN: No changes made.'))
            self.stdout.write('Run without --dry-run to update the data.')
            return
        
        if not auto_fill:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'To update these members, you can either:'
            ))
            self.stdout.write('1. Update them manually through the admin interface')
            self.stdout.write('2. Run with --auto-fill to generate random test data')
            self.stdout.write('3. Update the database directly')
            return
        
        # Auto-fill with random data for testing
        self.stdout.write('')
        self.stdout.write('Auto-filling with random test data...')
        
        with transaction.atomic():
            updated_count = 0
            for member in members_without_data:
                if not member.birth_date:
                    # Generate random birth date between 18-65 years ago
                    years_ago = random.randint(18, 65)
                    birth_year = date.today().year - years_ago
                    birth_month = random.randint(1, 12)
                    birth_day = random.randint(1, 28)  # Safe day for all months
                    member.birth_date = date(birth_year, birth_month, birth_day)
                
                if not member.gender:
                    # Randomly assign gender
                    member.gender = random.choice(['MALE', 'FEMALE'])
                
                member.save()
                updated_count += 1
                
                self.stdout.write(f'  ✓ Updated {member.full_name}')
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} members!')
        )
        self.stdout.write('You can now view the Church Report to see the demographic breakdown.')
