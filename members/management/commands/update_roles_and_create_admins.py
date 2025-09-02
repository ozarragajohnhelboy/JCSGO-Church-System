from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from members.models import Church, Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Update roles and create SUPER_ADMIN role for existing system'

    def handle(self, *args, **options):
        self.stdout.write('Updating roles and creating SUPER_ADMIN...')
        
        # Create SUPER_ADMIN role if it doesn't exist
        super_admin_role, created = Role.objects.get_or_create(
            name='SUPER_ADMIN',
            defaults={'description': 'Super Admin with full access to all churches'}
        )
        if created:
            self.stdout.write('Created SUPER_ADMIN role')
        else:
            self.stdout.write('SUPER_ADMIN role already exists')
        
        # Update ADMIN role description
        try:
            admin_role = Role.objects.get(name='ADMIN')
            admin_role.description = 'Church Admin with full access to their specific church'
            admin_role.save()
            self.stdout.write('Updated ADMIN role description')
        except Role.DoesNotExist:
            self.stdout.write('ADMIN role not found')
        
        # Remove CHURCH_LEADER role if it exists
        try:
            church_leader_role = Role.objects.get(name='CHURCH_LEADER')
            
            # Change users with CHURCH_LEADER role to ADMIN role
            users_with_role = User.objects.filter(role=church_leader_role)
            if users_with_role.exists():
                for user in users_with_role:
                    user.role = admin_role
                    user.save()
                self.stdout.write(f'Changed {users_with_role.count()} users from CHURCH_LEADER to ADMIN role')
            
            church_leader_role.delete()
            self.stdout.write('Removed CHURCH_LEADER role')
        except Role.DoesNotExist:
            self.stdout.write('CHURCH_LEADER role not found')
        
        # Update existing superuser to have SUPER_ADMIN role
        superusers = User.objects.filter(is_superuser=True)
        for superuser in superusers:
            if superuser.role != super_admin_role:
                superuser.role = super_admin_role
                superuser.save()
                self.stdout.write(f'Updated {superuser.email} to SUPER_ADMIN role')
        
        # Create a church admin for each church if they don't exist
        churches = Church.objects.filter(is_active=True)
        for church in churches:
            admin_email = f'admin@{church.domain}.jcsgo.com'
            
            if not User.objects.filter(email=admin_email).exists():
                # Create church admin user
                admin_user = User.objects.create_user(
                    email=admin_email,
                    first_name='Church',
                    last_name='Admin',
                    password='admin123456',
                    church=church,
                    role=admin_role,
                    is_staff=True,
                )
                self.stdout.write(f'Created church admin: {admin_user.email} for {church.name}')
            else:
                self.stdout.write(f'Church admin already exists for {church.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Role update completed successfully!')
        ) 