from django.core.management.base import BaseCommand
from django.db import transaction
from members.models import CustomUser, NewFriend, RegularMember


class Command(BaseCommand):
    help = 'Clean up member profile inconsistencies where users have both NewFriend and RegularMember profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find users with both profiles
        users_with_both_profiles = []
        
        for user in CustomUser.objects.all():
            has_new_friend = hasattr(user, 'new_friend_profile')
            has_regular_member = hasattr(user, 'regular_member_profile')
            
            if has_new_friend and has_regular_member:
                users_with_both_profiles.append(user)
        
        if not users_with_both_profiles:
            self.stdout.write(self.style.SUCCESS('No users with inconsistent profiles found!'))
            return
        
        self.stdout.write(f'Found {len(users_with_both_profiles)} users with both profiles:')
        
        for user in users_with_both_profiles:
            self.stdout.write(f'  - {user.full_name} (ID: {user.id})')
            self.stdout.write(f'    is_new_friend: {user.is_new_friend}')
            self.stdout.write(f'    NewFriend profile: {hasattr(user, "new_friend_profile")}')
            self.stdout.write(f'    RegularMember profile: {hasattr(user, "regular_member_profile")}')
            self.stdout.write('')
        
        if not dry_run:
            self.stdout.write('Cleaning up inconsistent profiles...')
            
            with transaction.atomic():
                for user in users_with_both_profiles:
                    if user.is_new_friend:
                        # User should be a new friend, remove RegularMember profile
                        if hasattr(user, 'regular_member_profile'):
                            user.regular_member_profile.delete()
                            self.stdout.write(f'  - Removed RegularMember profile for {user.full_name}')
                    else:
                        # User should be a regular member, remove NewFriend profile
                        if hasattr(user, 'new_friend_profile'):
                            user.new_friend_profile.delete()
                            self.stdout.write(f'  - Removed NewFriend profile for {user.full_name}')
            
            self.stdout.write(self.style.SUCCESS('Profile cleanup completed successfully!'))
        else:
            self.stdout.write(self.style.WARNING('Run without --dry-run to actually clean up the profiles')) 