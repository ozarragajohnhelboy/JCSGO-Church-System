from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from members.models import Church, Role
from churches.models import ChurchSettings

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial data for JCSGO Church Management System'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create roles
        roles_data = [
            {'name': 'ADMIN', 'description': 'Super Admin with full access'},
            {'name': 'CHURCH_LEADER', 'description': 'Church Leader with local admin access'},
            {'name': 'VSL', 'description': 'Vision Servant Leader'},
            {'name': 'CSL', 'description': 'Cell Servant Leader'},
            {'name': 'CL', 'description': 'Cell Leader'},
            {'name': 'CM', 'description': 'Cell Member'},
            {'name': 'NEW_FRIEND', 'description': 'New Friend (1st-5th timer)'},
        ]
        
        roles = {}
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            roles[role.name] = role
            if created:
                self.stdout.write(f'Created role: {role.name}')
            else:
                self.stdout.write(f'Role already exists: {role.name}')
        
        # Create churches
        churches_data = [
            # Region 4A (Rodriguez/Montalban, Rizal)
            {
                'name': 'JCSGO Kasiglahan',
                'location': 'Kasiglahan, Rodriguez (Montalban), Rizal',
                'domain': 'kasiglahan',
            },
            {
                'name': 'JCSGO San Jose',
                'location': 'San Jose, Rodriguez (Montalban), Rizal',
                'domain': 'sanjose',
            },
            {
                'name': 'JCSGO Christin Ville',
                'location': 'Christin Ville, Rodriguez (Montalban), Rizal',
                'domain': 'christinville',
            },
            {
                'name': 'JCSGO Tabak',
                'location': 'Tabak, Rodriguez (Montalban), Rizal',
                'domain': 'tabak',
            },
            # Central Region (Cubao, Quezon City, Metro Manila)
            {
                'name': 'JCSGO 10am Family',
                'location': 'Cubao, Quezon City, Metro Manila',
                'domain': '10amfamily',
            },
            {
                'name': 'JCSGO 3pm Family',
                'location': 'Cubao, Quezon City, Metro Manila',
                'domain': '3pmfamily',
            },
        ]
        
        churches = {}
        for church_data in churches_data:
            church, created = Church.objects.get_or_create(
                domain=church_data['domain'],
                defaults={
                    'name': church_data['name'],
                    'location': church_data['location'],
                }
            )
            churches[church.domain] = church
            if created:
                self.stdout.write(f'Created church: {church.name}')
            else:
                self.stdout.write(f'Church already exists: {church.name}')
            
            # Create church settings
            settings, created = ChurchSettings.objects.get_or_create(
                church=church,
                defaults={
                    'allow_public_registration': True,
                    'require_email_verification': True,
                    'require_admin_approval': False,
                }
            )
            if created:
                self.stdout.write(f'Created settings for: {church.name}')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            admin_user = User.objects.create_superuser(
                email='admin@jcsgo.com',
                first_name='Super',
                last_name='Admin',
                password='admin123456',
                church=churches['kasiglahan'],
                role=roles['ADMIN'],
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created superuser: {admin_user.email}')
            )
        else:
            self.stdout.write('Superuser already exists')
        
        self.stdout.write(
            self.style.SUCCESS('Initial data setup completed successfully!')
        ) 