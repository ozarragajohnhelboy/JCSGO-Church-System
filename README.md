# JCSGO Church Management System

A comprehensive multi-tenant church management system built with Django, designed to handle multiple church branches with role-based access control and member management.

## 🎯 Project Overview

This system manages church members, groups, and activities across multiple church branches with the following key features:

- **Multi-tenant Architecture**: Each church operates independently
- **Role-based Access Control**: Different permissions for different user roles
- **Member Management**: Track new friends and regular members
- **Group Management**: Care groups and ministry groups
- **Activity Logging**: Comprehensive audit trail
- **Import/Export**: Data management capabilities

## 🏗️ Architecture

### Phase 1: Foundation (Completed ✅)
- Multi-tenant architecture with church-specific domains
- Custom user model with church and role integration
- Church-specific authentication system
- Role-based dashboard system
- Email-based church detection

### Phase 2: Core Models (Completed ✅)
- Enhanced database models with comprehensive relationships
- Import/Export functionality for all data types
- Advanced member management features
- Group management with capacity tracking
- Activity logging and analytics
- Follow-up tracking for new friends

## 📊 Database Models

### Core Models
1. **Church** - Church branches with domain-based identification
2. **Role** - User roles with permission levels
3. **CustomUser** - Extended user model with church and role integration
4. **NewFriend** - Extended tracking for new members (1st-5th timer)
5. **RegularMember** - Extended tracking for regular members
6. **Group** - Care groups and ministry groups
7. **ActivityLog** - Comprehensive activity tracking

### Church-Specific Models
1. **ChurchSettings** - Church-specific configurations
2. **ChurchAnnouncement** - Church announcements and notifications

## 👥 User Roles

1. **SUPER ADMIN** - Super admin with full access to all churches
2. **ADMIN** - Church-level admin with full access to their specific church
3. **VSL** - Vine Servant Leader
4. **CSL** - Cluster Servant Leader
5. **CL** - Care Leader
6. **CM** - Care Member
7. **NEW_FRIEND** - New Friend (1st-5th timer)

## 🚀 Features

### Member Management
- **Member Profiles**: Comprehensive member information
- **New Friends Tracking**: Timer status and follow-up management
- **Regular Members**: Role assignment and group membership
- **Search & Filter**: Advanced search capabilities
- **Bulk Operations**: Mass updates and exports

### Group Management
- **Care Groups**: Small group management
- **Ministry Groups**: Ministry team management
- **Capacity Tracking**: Member limits and availability
- **Meeting Scheduling**: Meeting times and locations
- **Member Assignment**: Add/remove members from groups

### Activity Tracking
- **Login/Logout**: User session tracking
- **Profile Updates**: Member information changes
- **Role Changes**: Permission updates
- **Group Activities**: Join/leave events
- **Attendance**: Service attendance recording
- **Follow-up**: New friend engagement tracking

### Data Management
- **Import/Export**: CSV, XLSX, JSON formats
- **Bulk Operations**: Mass data updates
- **Data Validation**: Comprehensive error checking
- **Audit Trail**: Complete activity history

### Analytics & Reporting
- **Church Statistics**: Member counts and growth
- **Activity Analytics**: User engagement metrics
- **Growth Trends**: Monthly member growth
- **Group Analytics**: Group performance metrics

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Django 5.2+
- SQLite (development) / PostgreSQL (production)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd HB

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup initial data
python manage.py setup_initial_data

# Run development server
python manage.py runserver
```

## 📁 Project Structure

```
HB/
├── church/                 # Main Django project
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── churches/              # Church management app
│   ├── models.py         # Church-specific models
│   ├── views.py          # Church views
│   ├── forms.py          # Church forms
│   └── utils.py          # Utility functions
├── members/               # Member management app
│   ├── models.py         # Core models
│   ├── views.py          # Member views
│   ├── forms.py          # Member forms
│   ├── admin.py          # Admin interface
│   └── management/       # Management commands
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS)
└── requirements.txt      # Python dependencies
```

## 🔧 Management Commands

### Data Setup
```bash
# Setup initial data (churches, roles, superuser)
python manage.py setup_initial_data

# Update church locations
python manage.py update_church_locations
```

### Import/Export
```bash
# Export all data
python manage.py import_export_data export all --format csv

# Export specific model
python manage.py import_export_data export user --format xlsx

# Import data
python manage.py import_export_data import user --file users.csv

# Export with church filter
python manage.py import_export_data export user --church kasiglahan
```

## 🌐 URL Structure

### Church Management
- `/` - Church selection
- `/<church-domain>/login/` - Church-specific login
- `/<church-domain>/register/` - Church-specific registration
- `/dashboard/` - User dashboard

### Member Management
- `/members/` - Member list
- `/members/<id>/` - Member detail
- `/new-friends/` - New friends list
- `/regular-members/` - Regular members list
- `/groups/` - Group list
- `/groups/<id>/` - Group detail
- `/activity-logs/` - Activity logs
- `/statistics/` - Church statistics

### Admin Interface
- `/admin/` - Django admin interface
- `/admin/members/` - Member management
- `/admin/churches/` - Church management

## 🔐 Security Features

- **Multi-tenant Isolation**: Church data is completely isolated
- **Role-based Permissions**: Granular access control
- **Activity Logging**: Complete audit trail
- **CSRF Protection**: Built-in Django security
- **Input Validation**: Comprehensive form validation

## 📊 Data Import/Export

### Supported Formats
- **CSV**: Comma-separated values
- **XLSX**: Excel spreadsheets
- **JSON**: JavaScript Object Notation

### Exportable Data
- Churches and settings
- User roles and permissions
- Member profiles and relationships
- Group information and membership
- Activity logs and analytics

### Import Features
- **Data Validation**: Comprehensive error checking
- **Relationship Mapping**: Foreign key resolution
- **Duplicate Detection**: Prevents data conflicts
- **Batch Processing**: Efficient bulk operations

## 🎨 User Interface

### Dashboard Types
1. **Super Admin Dashboard**: System-wide overview
2. **Church Admin Dashboard**: Church-specific management
3. **Church Leader Dashboard**: Group and member oversight
4. **Member Dashboard**: Personal information and activities

### Key Features
- **Responsive Design**: Works on all devices
- **Bootstrap 5**: Modern UI framework
- **Interactive Elements**: AJAX-powered updates
- **Search & Filter**: Advanced data filtering
- **Pagination**: Efficient data display

## 🔄 API Endpoints

### AJAX Endpoints
- `POST /members/ajax/update-timer-status/<id>/` - Update timer status
- `POST /members/ajax/record-attendance/<id>/` - Record attendance
- `POST /members/ajax/update-follow-up/<id>/` - Update follow-up status
- `POST /members/ajax/add-to-group/<user_id>/<group_id>/` - Add to group
- `POST /members/ajax/remove-from-group/<user_id>/<group_id>/` - Remove from group

### Export Endpoints
- `GET /members/export/?format=csv` - Export members data
- `GET /members/export/?format=xlsx` - Export as Excel
- `GET /members/export/?format=json` - Export as JSON

## 📈 Analytics & Reporting

### Member Analytics
- Total member counts
- New friends vs regular members
- Role distribution
- Growth trends
- Attendance patterns

### Group Analytics
- Group capacity utilization
- Member distribution
- Meeting attendance
- Group performance metrics

### Activity Analytics
- User engagement metrics
- Login patterns
- Feature usage statistics
- System activity overview

## 🚀 Deployment

### Development
```bash
python manage.py runserver
```

### Production
```bash
# Collect static files
python manage.py collectstatic

# Run with production server
gunicorn church.wsgi:application
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔮 Future Enhancements

### Phase 3: Advanced Features (Planned)
- Event management system
- Attendance tracking with QR codes
- Financial management
- Communication tools
- Mobile app integration

### Phase 4: Analytics & Reporting (Planned)
- Advanced analytics dashboard
- Custom report generation
- Data visualization
- Predictive analytics
- Performance metrics

---

**Built with ❤️ for JCSGO Churches**
