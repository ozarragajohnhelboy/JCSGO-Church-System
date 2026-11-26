from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0017_attendance_service_setup'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupLeaveRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('church', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_leave_requests', to='members.church')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_requests', to='members.group')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_leave_requests', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_leave_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Group Leave Request',
                'verbose_name_plural': 'Group Leave Requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='groupleaverequest',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'PENDING')), fields=('member', 'group'), name='unique_pending_group_leave'),
        ),
    ]
