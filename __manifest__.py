{
    "name": "Activity Report",
    "version": "12.0.1.0.0",
    "summary": "Report of all user activities in the system",
    "description": """
        This module provides a report listing all activities (mail.activity) 
        with filters for users, models, and date ranges.
    """,
    "category": "Reporting",
    "depends": ["base", "mail"],
    "data": [
        "security/activity_report_security.xml",
        "security/ir.model.access.csv",
        "views/activity_report_views.xml",
        "views/menu.xml",
    ],
    "application": True,
}
