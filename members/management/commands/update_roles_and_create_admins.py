from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from members.models import Church, Role
from churches.models import ChurchSettings

User = get_user_model()


class Command(BaseCommand):
    help = 'Update role structure and create admin accounts for each church'

    def handle(self, *args, **options):
        self.stdout.write('Updating role structure...')
        
        # Update role descriptions
        role_updates = {
            'VSL': 'Vine Servant Leader',
            'CSL': 'Cluster Servant Leader', 
            'CL': 'Care Leader',
            'CM': 'Care Member',
        }
        
        for role_name, new_description in role_updates.items():
            try:
                role = Role.objects.get(name=role_name)
                role.description = new_description
                role.save()
                self.stdout.write(f'Updated {role_name}: {new_description}')
            except Role.DoesNotExist:
                self.stdout.write(f'Role {role_name} not found')
        
        # Remove CHURCH_LEADER role if it exists
        try:
            church_leader_role = Role.objects.get(name='CHURCH_LEADER')
            # Check if any users have this role
            users_with_role = User.objects.filter(role=church_leader_role)
            if users_with_role.exists():
                self.stdout.write(f'Warning: {users_with_role.count()} users still have CHURCH_LEADER role')
                # Change them to ADMIN role
                admin_role = Role.objects.get(name='ADMIN')
                users_with_role.update(role=admin_role)
                self.stdout.write('Changed CHURCH_LEADER users to ADMIN role')
            
            church_leader_role.delete()
            self.stdout.write('Removed CHURCH_LEADER role')
        except Role.DoesNotExist:
            self.stdout.write('CHURCH_LEADER role not found')
        
        # Get all active churches
        churches = Church.objects.filter(is_active=True)
        admin_role = Role.objects.get(name='ADMIN')
        
        self.stdout.write('Creating admin accounts for each church...')
        
        for church in churches:
            admin_email = f'admin@{church.domain}.jcsgo.com'
            
            # Check if admin account already exists
            if User.objects.filter(email=admin_email).exists():
                self.stdout.write(f'Admin account already exists for {church.name}: {admin_email}')
                continue
            
            # Create admin account
            try:
                admin_user = User.objects.create_user(
                    email=admin_email,
                    first_name='Admin',
                    last_name=church.name.replace('JCSGO ', ''),
                    password='admin123456',
                    church=church,
                    role=admin_role,
                    is_staff=True,
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created admin account for {church.name}: {admin_email}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create admin account for {church.name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Role structure update and admin account creation completed!')
        ) 