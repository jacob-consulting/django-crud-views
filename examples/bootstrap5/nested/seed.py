from django.contrib.auth import get_user_model

from nested.models import Company, Department, Employee, Office
from project.seeding import grant_model_perms

COMPANIES = {
    "Acme Corp": {
        "city": "Springfield",
        "departments": {
            "Engineering": ["Jo Miller", "Sam Chen"],
            "Support": ["Alex Novak"],
        },
        "offices": ["Headquarters", "Lab Annex"],
    },
    "Globex": {
        "city": "Cypress Creek",
        "departments": {"Sales": ["Kim Braun"]},
        "offices": ["Main Office"],
    },
}


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        for model in (Company, Department, Employee, Office):
            grant_model_perms(user, model)
    for name, data in COMPANIES.items():
        company, _ = Company.objects.get_or_create(name=name, defaults={"city": data["city"]})
        for department_name, employees in data["departments"].items():
            department, _ = Department.objects.get_or_create(company=company, name=department_name)
            for employee_name in employees:
                email = f"{employee_name.split()[0].lower()}@{name.split()[0].lower()}.example"
                Employee.objects.get_or_create(department=department, name=employee_name, defaults={"email": email})
        for office_name in data["offices"]:
            Office.objects.get_or_create(company=company, name=office_name)
