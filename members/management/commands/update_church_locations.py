from django.core.management.base import BaseCommand
from members.models import Church


class Command(BaseCommand):
    help = 'Update church locations with correct addresses'

    def handle(self, *args, **options):
        self.stdout.write('Updating church locations...')
        
        # Update church locations
        church_updates = {
            'kasiglahan': 'Kasiglahan, Rodriguez (Montalban), Rizal',
            'sanjose': 'San Jose, Rodriguez (Montalban), Rizal',
            'christinville': 'Christin Ville, Rodriguez (Montalban), Rizal',
            'tabak': 'Tabak, Rodriguez (Montalban), Rizal',
            '10amfamily': 'Cubao, Quezon City, Metro Manila',
            '3pmfamily': 'Cubao, Quezon City, Metro Manila',
        }
        
        for domain, location in church_updates.items():
            try:
                church = Church.objects.get(domain=domain)
                church.location = location
                church.save()
                self.stdout.write(f'Updated {church.name}: {location}')
            except Church.DoesNotExist:
                self.stdout.write(f'Church with domain {domain} not found')
        
        self.stdout.write(
            self.style.SUCCESS('Church locations updated successfully!')
        ) 