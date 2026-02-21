# EstateFlow - Real Estate CRM

A comprehensive Customer Relationship Management system for real estate professionals built with Flask. This is a **private/personal use** CRM - there is no public registration. Only the admin can create staff accounts.

## Features

### 📊 Dashboard
- Overview of key metrics (clients, properties, deals, revenue)
- Recent clients and properties at a glance
- Upcoming tasks and scheduled showings

### 👥 Client Management
- Add, edit, and delete clients
- Track client type (buyer/seller/both)
- Manage client status (lead, prospect, active, closed)
- Set budget ranges and preferred locations
- Track lead sources
- Log interactions (calls, emails, meetings, showings)

### 🏠 Property Listings
- Full property management (add, edit, delete)
- Property types: house, apartment, condo, townhouse, land, commercial
- Listing types: for sale or rent
- Track status: available, pending, sold, rented
- Property details: bedrooms, bathrooms, sqft, lot size, year built
- Schedule property showings

### 🤝 Deal Tracking
- Create and manage deals
- Pipeline view (initiated → negotiation → under contract → closed)
- Track offer and final prices
- Calculate commission automatically
- Set closing dates

### ✅ Task Management
- Create tasks with priorities (low, medium, high, urgent)
- Set due dates
- Mark tasks as complete
- Filter by status and priority

### 📈 Reports & Analytics
- Monthly sales and commission charts
- Lead source breakdown
- Property status breakdown
- Year-to-date performance metrics

### 👔 Staff Management (Admin Only)
- Add, edit, and manage staff members
- Assign roles: Staff, Manager, Admin
- Track staff performance and commissions
- Activate/deactivate accounts
- View individual staff statistics

## Installation

1. **Clone or download the project**

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   Navigate to `http://localhost:5000`

## Admin Account

An admin account is automatically created when you first run the application:

- **Username:** admin
- **Password:** admin123

⚠️ **Important:** Change the admin password after first login!

## User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access + Staff management |
| **Manager** | Full access to CRM features |
| **Staff** | Access to own clients, properties, deals, tasks |

## Project Structure

```
real-estate-crm/
├── app.py              # Main Flask application with routes and models
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── login.html      # Login page
│   ├── dashboard.html  # Main dashboard
│   ├── clients.html    # Clients list
│   ├── client_form.html    # Add/edit client
│   ├── client_detail.html  # Client details
│   ├── properties.html     # Properties list
│   ├── property_form.html  # Add/edit property
│   ├── property_detail.html # Property details
│   ├── deals.html      # Deals list
│   ├── deal_form.html  # Add/edit deal
│   ├── tasks.html      # Tasks list
│   ├── reports.html    # Reports & analytics
│   └── staff/          # Staff management templates (admin only)
│       ├── staff_list.html
│       ├── staff_form.html
│       └── staff_detail.html
└── instance/           # SQLite database (created on first run)
```

## Database

The application uses SQLite for simplicity. The database file is created automatically in the `instance` folder when you first run the application.

### Models:
- **User** - Staff accounts with roles and permissions
- **Client** - Client information and preferences
- **Property** - Property listings
- **Deal** - Transaction tracking
- **Interaction** - Client interaction history
- **Task** - Task management
- **Showing** - Property showing schedules

## Tech Stack

- **Backend:** Flask 3.0, Flask-SQLAlchemy, Flask-Login
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **Styling:** Custom CSS with CSS variables
- **Charts:** Chart.js
- **Icons:** Font Awesome 6
- **Fonts:** DM Sans, Playfair Display (Google Fonts)
