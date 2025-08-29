from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from django.conf import settings
import os
import csv
from datetime import datetime

from members.models import Church, Role, CustomUser, NewFriend, RegularMember, Group, ActivityLog
from members.admin import (
    ChurchResource, RoleResource, CustomUserResource, 
    NewFriendResource, RegularMemberResource, GroupResource, ActivityLogResource
)


class Command(BaseCommand):
    help = 'Import or export church data in various formats (CSV, XLSX, JSON)'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['import', 'export'],
            help='Action to perform: import or export'
        )
        parser.add_argument(
            'model',
            choices=['church', 'role', 'user', 'newfriend', 'regularmember', 'group', 'activitylog', 'all'],
            help='Model to import/export'
        )
        parser.add_argument(
            '--format',
            choices=['csv', 'xlsx', 'json'],
            default='csv',
            help='File format (default: csv)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Input/output file path'
        )
        parser.add_argument(
            '--church',
            type=str,
            help='Filter by church domain (for export)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        action = options['action']
        model = options['model']
        file_format = options['format']
        file_path = options['file']
        church_filter = options['church']
        dry_run = options['dry_run']

        # Generate default file path if not provided
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if action == 'export':
                file_path = f'church_data_{model}_{timestamp}.{file_format}'
            else:
                file_path = f'import_{model}_{timestamp}.{file_format}'

        # Get resource class based on model
        resource_map = {
            'church': ChurchResource,
            'role': RoleResource,
            'user': CustomUserResource,
            'newfriend': NewFriendResource,
            'regularmember': RegularMemberResource,
            'group': GroupResource,
            'activitylog': ActivityLogResource,
        }

        if model == 'all':
            self.handle_all_models(action, file_format, file_path, church_filter, dry_run)
        else:
            resource_class = resource_map.get(model)
            if not resource_class:
                raise CommandError(f'Unknown model: {model}')
            
            self.handle_single_model(action, model, resource_class, file_format, file_path, church_filter, dry_run)

    def handle_single_model(self, action, model, resource_class, file_format, file_path, church_filter, dry_run):
        """Handle import/export for a single model"""
        resource = resource_class()
        
        if action == 'export':
            self.export_data(model, resource, file_format, file_path, church_filter)
        else:  # import
            self.import_data(model, resource, file_format, file_path, dry_run)

    def handle_all_models(self, action, file_format, file_path, church_filter, dry_run):
        """Handle import/export for all models"""
        models = ['church', 'role', 'user', 'newfriend', 'regularmember', 'group', 'activitylog']
        
        if action == 'export':
            # Create directory for exports
            export_dir = f'church_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.makedirs(export_dir, exist_ok=True)
            
            for model in models:
                resource_class = {
                    'church': ChurchResource,
                    'role': RoleResource,
                    'user': CustomUserResource,
                    'newfriend': NewFriendResource,
                    'regularmember': RegularMemberResource,
                    'group': GroupResource,
                    'activitylog': ActivityLogResource,
                }[model]
                
                model_file_path = os.path.join(export_dir, f'{model}.{file_format}')
                self.export_data(model, resource_class(), file_format, model_file_path, church_filter)
            
            self.stdout.write(
                self.style.SUCCESS(f'All data exported to directory: {export_dir}')
            )
        else:  # import
            # Import in dependency order
            import_order = ['church', 'role', 'user', 'newfriend', 'regularmember', 'group', 'activitylog']
            
            for model in import_order:
                resource_class = {
                    'church': ChurchResource,
                    'role': RoleResource,
                    'user': CustomUserResource,
                    'newfriend': NewFriendResource,
                    'regularmember': RegularMemberResource,
                    'group': GroupResource,
                    'activitylog': ActivityLogResource,
                }[model]
                
                model_file_path = os.path.join(file_path, f'{model}.{file_format}')
                if os.path.exists(model_file_path):
                    self.import_data(model, resource_class(), file_format, model_file_path, dry_run)
                else:
                    self.stdout.write(
                        self.style.WARNING(f'File not found: {model_file_path}')
                    )

    def export_data(self, model, resource, file_format, file_path, church_filter):
        """Export data to file"""
        try:
            # Apply church filter if specified
            if church_filter and hasattr(resource.Meta.model, 'church'):
                queryset = resource.Meta.model.objects.filter(church__domain=church_filter)
            elif church_filter and model == 'user':
                queryset = CustomUser.objects.filter(church__domain=church_filter)
            else:
                queryset = resource.Meta.model.objects.all()

            # Export data
            if file_format == 'csv':
                dataset = resource.export(queryset)
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    f.write(dataset.csv)
            elif file_format == 'xlsx':
                dataset = resource.export(queryset)
                dataset.xlsx.write(file_path)
            elif file_format == 'json':
                dataset = resource.export(queryset)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(dataset.json)

            count = queryset.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully exported {count} {model} records to {file_path}'
                )
            )

        except Exception as e:
            raise CommandError(f'Export failed: {str(e)}')

    def import_data(self, model, resource, file_format, file_path, dry_run):
        """Import data from file"""
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')

        try:
            # Read data from file
            if file_format == 'csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    dataset = resource.import_data(f.read(), dry_run=dry_run)
            elif file_format == 'xlsx':
                dataset = resource.import_data(open(file_path, 'rb'), dry_run=dry_run)
            elif file_format == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    dataset = resource.import_data(f.read(), dry_run=dry_run)

            # Report results
            if dataset.has_errors():
                self.stdout.write(
                    self.style.ERROR(f'Import completed with errors for {model}:')
                )
                for row in dataset.rows:
                    if row.errors:
                        self.stdout.write(f'Row {row.number}: {row.errors}')
            else:
                action = 'Would import' if dry_run else 'Imported'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action} {dataset.total_rows} {model} records from {file_path}'
                    )
                )

        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')

    def create_sample_export(self):
        """Create sample export files for reference"""
        sample_dir = 'sample_exports'
        os.makedirs(sample_dir, exist_ok=True)
        
        # Export one record of each type as sample
        models = [
            ('church', ChurchResource, Church.objects.first()),
            ('role', RoleResource, Role.objects.first()),
            ('user', CustomUserResource, CustomUser.objects.first()),
            ('newfriend', NewFriendResource, NewFriend.objects.first()),
            ('regularmember', RegularMemberResource, RegularMember.objects.first()),
            ('group', GroupResource, Group.objects.first()),
            ('activitylog', ActivityLogResource, ActivityLog.objects.first()),
        ]
        
        for model_name, resource_class, instance in models:
            if instance:
                resource = resource_class()
                dataset = resource.export([instance])
                
                # Export in all formats
                for fmt in ['csv', 'xlsx', 'json']:
                    file_path = os.path.join(sample_dir, f'sample_{model_name}.{fmt}')
                    if fmt == 'csv':
                        with open(file_path, 'w', newline='', encoding='utf-8') as f:
                            f.write(dataset.csv)
                    elif fmt == 'xlsx':
                        dataset.xlsx.write(file_path)
                    elif fmt == 'json':
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(dataset.json)
        
        self.stdout.write(
            self.style.SUCCESS(f'Sample export files created in {sample_dir}')
        ) 