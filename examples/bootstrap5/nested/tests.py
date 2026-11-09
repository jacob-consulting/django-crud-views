from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from nested.models import Company, Department, Employee, Office


class NestedTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.acme = Company.objects.create(name="Acme Corp", city="Springfield")
        cls.globex = Company.objects.create(name="Globex", city="Cypress Creek")
        cls.engineering = Department.objects.create(company=cls.acme, name="Engineering")
        cls.sales = Department.objects.create(company=cls.globex, name="Sales")
        cls.jo = Employee.objects.create(department=cls.engineering, name="Jo Miller", email="jo@acme.example")
        cls.hq = Office.objects.create(company=cls.acme, name="Headquarters")

    def setUp(self):
        self.client.force_login(self.admin)


class CompanyTest(NestedTestCase):
    def test_list_renders_with_snippets(self):
        resp = self.client.get(reverse("company-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Acme Corp")
        self.assertContains(resp, "snippet-panels")

    def test_create(self):
        resp = self.client.post(reverse("company-create"), {"name": "Initech", "city": "Austin"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Company.objects.filter(name="Initech").exists())


class DepartmentTest(NestedTestCase):
    def test_list_is_filtered_to_parent_company(self):
        resp = self.client.get(reverse("department-list", kwargs={"company_pk": self.acme.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Engineering")
        self.assertNotContains(resp, "Sales")  # belongs to Globex

    def test_create_sets_parent_fk_automatically(self):
        url = reverse("department-create", kwargs={"company_pk": self.acme.pk})
        resp = self.client.post(url, {"name": "Research"})
        self.assertEqual(resp.status_code, 302)
        department = Department.objects.get(name="Research")
        self.assertEqual(department.company, self.acme)


class EmployeeTest(NestedTestCase):
    def test_grandchild_list_url_carries_both_parent_pks(self):
        url = reverse(
            "employee-list",
            kwargs={"company_pk": self.acme.pk, "department_pk": self.engineering.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Jo Miller")

    def test_create_sets_department(self):
        url = reverse(
            "employee-create",
            kwargs={"company_pk": self.acme.pk, "department_pk": self.engineering.pk},
        )
        resp = self.client.post(url, {"name": "Sam Chen", "email": "sam@acme.example"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Employee.objects.get(name="Sam Chen").department, self.engineering)


class OfficeTest(NestedTestCase):
    def test_second_child_list(self):
        resp = self.client.get(reverse("office-list", kwargs={"company_pk": self.acme.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Headquarters")


class NestedSeedTest(TestCase):
    def test_seed_twice(self):
        from django.core.management import call_command

        call_command("seed")
        counts = (Company.objects.count(), Department.objects.count(), Employee.objects.count())
        call_command("seed")
        self.assertEqual((Company.objects.count(), Department.objects.count(), Employee.objects.count()), counts)
        self.assertGreater(Company.objects.count(), 0)

    def test_seeded_alice_passes_the_ancestor_gates(self):
        from django.core.management import call_command

        call_command("seed")
        self.client.force_login(get_user_model().objects.get(username="alice"))
        acme = Company.objects.get(name="Acme Corp")
        kwargs = {"company_pk": acme.pk}
        self.assertEqual(self.client.get(reverse("department-list", kwargs=kwargs)).status_code, 200)
        resp = self.client.post(reverse("department-create", kwargs=kwargs), {"name": "Research"})
        self.assertEqual(resp.status_code, 302)  # the seed needs no change for ancestor authorization


class NestedAncestorAuthorizationTest(TestCase):
    """Each nested request is also authorized against its ancestors (default policy: Read needs view on the
    parent, Write needs change on it). Plain users, not superusers: a superuser bypasses every gate."""

    @classmethod
    def setUpTestData(cls):
        from project.seeding import grant_model_perms

        User = get_user_model()
        cls.acme = Company.objects.create(name="Acme Corp", city="Springfield")
        cls.engineering = Department.objects.create(company=cls.acme, name="Engineering")

        cls.editor = User.objects.create_user(username="editor-test", password="pw")
        for model in (Company, Department, Employee, Office):
            grant_model_perms(cls.editor, model)  # same as the seed
        cls.dept_only = User.objects.create_user(username="dept-only-test", password="pw")
        grant_model_perms(cls.dept_only, Department)
        cls.company_viewer = User.objects.create_user(username="company-viewer-test", password="pw")
        grant_model_perms(cls.company_viewer, Company, actions=("view",))
        grant_model_perms(cls.company_viewer, Department)
        grant_model_perms(cls.company_viewer, Employee)

    def test_editor_with_company_change_can_list_and_create_departments(self):
        self.client.force_login(self.editor)
        kwargs = {"company_pk": self.acme.pk}
        self.assertEqual(self.client.get(reverse("department-list", kwargs=kwargs)).status_code, 200)
        resp = self.client.post(reverse("department-create", kwargs=kwargs), {"name": "Research"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Department.objects.get(name="Research").company, self.acme)

    def test_department_permissions_alone_do_not_open_the_nested_urls(self):
        self.client.force_login(self.dept_only)
        kwargs = {"company_pk": self.acme.pk}
        self.assertEqual(self.client.get(reverse("department-list", kwargs=kwargs)).status_code, 403)
        self.assertEqual(self.client.get(reverse("department-create", kwargs=kwargs)).status_code, 403)
        self.client.post(reverse("department-create", kwargs=kwargs), {"name": "Research"})
        self.assertFalse(Department.objects.filter(name="Research").exists())

    def test_company_view_reads_but_does_not_write_children(self):
        self.client.force_login(self.company_viewer)
        kwargs = {"company_pk": self.acme.pk}
        self.assertEqual(self.client.get(reverse("department-list", kwargs=kwargs)).status_code, 200)
        # full cascade: Department view + Company view
        employee_kwargs = {"company_pk": self.acme.pk, "department_pk": self.engineering.pk}
        self.assertEqual(self.client.get(reverse("employee-list", kwargs=employee_kwargs)).status_code, 200)
        # Write needs change on the Company
        self.assertEqual(self.client.get(reverse("department-create", kwargs=kwargs)).status_code, 403)
        resp = self.client.post(reverse("department-create", kwargs=kwargs), {"name": "Research"})
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Department.objects.filter(name="Research").exists())
