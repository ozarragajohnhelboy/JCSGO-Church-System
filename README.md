# JCSGO Church Management System

A comprehensive Django-based church management system for JCSGO (Jesus Christ the Savior Global Outreach) church branches.

## 🏢 Features

### Phase 1 - Foundation (Completed)

- ✅ **Multi-tenant Church System** - Support for multiple church branches
- ✅ **User Authentication** - Church-specific login with email domains
- ✅ **Role-based Access Control** - Super Admin, Church Admin, Leaders, Members
- ✅ **Registration System** - New member registration with role selection
- ✅ **Dashboard System** - Different dashboards for different user roles
- ✅ **Professional UI** - Bootstrap 5 with modern design

### User Roles

- **Super Admin** - Can view all church dashboards
- **Church Admin** - Manages their specific church
- **VSL** (Vine Servant Leader)
- **CSL** (Cluster Servant Leader)
- **CL** (Care Leader)
- **CM** (Care Member)
- **New Friend** (1st-5th timer)

### Church Branches

**Region 4A (Rodriguez, Rizal):**

- JCSGO Kasiglahan
- JCSGO San Jose
- JCSGO Christin Ville
- JCSGO Tabak

**Central Region (Cubao, Quezon City):**

- JCSGO 10am Family
- JCSGO 3pm Family

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- Git

### Installation

1. **Clone the repository**

```bash
git clone git@github.com:ozarragajohnhelboy/JCSGO-Church-System.git
cd JCSGO-Church-System
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run migrations**

```bash
python manage.py migrate
```

5. **Setup initial data**

```bash
python manage.py setup_initial_data
```

6. **Run the development server**

```bash
python manage.py runserver
```

7. **Access the application**
   - Open http://127.0.0.1:8000/
   - Select your church branch
   - Login or register

## 👤 Default Users

### Super Admin

- **Email:** admin@gmail.com
- **Password:** admin123

### Church Admins

- **JCSGO Kasiglahan:** admin@kasiglahan.jcsgo.com / admin123
- **JCSGO San Jose:** admin@sanjose.jcsgo.com / admin123
- **JCSGO Christin Ville:** admin@christinville.jcsgo.com / admin123
- **JCSGO Tabak:** admin@tabak.jcsgo.com / admin123
- **JCSGO 10am Family:** admin@10amfamily.jcsgo.com / admin123
- **JCSGO 3pm Family:** admin@3pmfamily.jcsgo.com / admin123

## 📊 Dashboard Features

### Super Admin Dashboard

- Overview of all church branches
- Total members across all churches
- Click to view individual church dashboards (modal)
- Quick actions for system management

### Church Admin Dashboard

- Church-specific statistics
- New Friends (1st-5th timer) tracking
- Regular Members breakdown by role
- Monthly registration charts
- Conversion rate tracking
- Recent activity logs

### Member Dashboard

- Personal status and information
- Church-specific information
- Quick actions based on role

## 🛠️ Technical Stack

- **Backend:** Django 4.2+
- **Frontend:** Bootstrap 5, jQuery
- **Database:** SQLite (development), PostgreSQL (production ready)
- **Authentication:** Django Allauth
- **Charts:** Chart.js
- **Icons:** Bootstrap Icons

## 📁 Project Structure

```
church/
├── church/                 # Main Django project
│   ├── settings.py        # Project settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── churches/              # Churches app
│   ├── models.py         # Church-related models
│   ├── views.py          # Church views
│   ├── forms.py          # Church forms
│   └── urls.py           # Church URLs
├── members/               # Members app
│   ├── models.py         # User and member models
│   ├── admin.py          # Django admin configuration
│   └── management/       # Custom management commands
├── static/                # Static files
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript files
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── churches/         # Church templates
│   └── account/          # Authentication templates
└── manage.py             # Django management script
```

## 🔧 Management Commands

### Setup Initial Data

```bash
python manage.py setup_initial_data
```

Creates:

- Default roles (NEW_FRIEND, CM, CL, CSL, VSL, ADMIN)
- Church branches
- Super admin user
- Church admin users

### Update Church Locations

```bash
python manage.py update_church_locations
```

Updates church locations based on domain names.

## 🎨 Customization

### Adding New Church Branches

1. Add church data in `members/management/commands/setup_initial_data.py`
2. Run `python manage.py setup_initial_data`

### Modifying User Roles

1. Update role choices in `members/models.py`
2. Update registration form in `churches/forms.py`
3. Run migrations if needed

### Styling

- Main CSS: `static/css/style.css`
- JavaScript: `static/js/main.js`
- Base template: `templates/base.html`

## 🔒 Security Features

- Role-based access control
- Church-specific data isolation
- Secure authentication with Django Allauth
- CSRF protection
- SQL injection prevention

## 📈 Future Features (Phase 2)

- Member management (import/export)
- Group management
- Timer status tracking
- Activity logging
- Reports and analytics
- Email notifications
- Mobile responsiveness improvements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is proprietary software for JCSGO Church Management System.

## 📞 Support

For support and questions, contact the development team.

---

**Built with ❤️ for JCSGO Church Management**
