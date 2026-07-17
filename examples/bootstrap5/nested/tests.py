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
