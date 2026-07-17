from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from crud_views_workflow.models import WorkflowInfo
from workflow.models import Campaign, CampaignState


class WorkflowTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
        cls.campaign = Campaign.objects.create(name="Spring Newsletter")

    def setUp(self):
        self.client.force_login(self.admin)


class CampaignWorkflowTest(WorkflowTestCase):
    def test_list_renders_with_snippets(self):
        resp = self.client.get(reverse("campaign-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Spring Newsletter")
        self.assertContains(resp, "snippet-panels")

    def test_workflow_view_offers_transition(self):
        resp = self.client.get(reverse("campaign-workflow", kwargs={"pk": self.campaign.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Activate")

    def test_activate_transition(self):
        url = reverse("campaign-workflow", kwargs={"pk": self.campaign.pk})
        resp = self.client.post(url, {"transition": "wf_activate", "comment": ""})
        self.assertEqual(resp.status_code, 302)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.state, CampaignState.ACTIVE)

    def test_transition_writes_audit_history(self):
        url = reverse("campaign-workflow", kwargs={"pk": self.campaign.pk})
        self.client.post(url, {"transition": "wf_activate", "comment": ""})
        self.assertTrue(
            WorkflowInfo.objects.filter(
                workflow_object_pk=str(self.campaign.pk),
                transition="wf_activate",
                state_old=CampaignState.DRAFT,
                state_new=CampaignState.ACTIVE,
            ).exists()
        )

    def test_cancel_requires_comment(self):
        url = reverse("campaign-workflow", kwargs={"pk": self.campaign.pk})
        resp = self.client.post(url, {"transition": "wf_cancel", "comment": ""})
        self.assertEqual(resp.status_code, 200)  # form error, re-rendered
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.state, CampaignState.DRAFT)

    def test_cancel_with_comment(self):
        url = reverse("campaign-workflow", kwargs={"pk": self.campaign.pk})
        resp = self.client.post(url, {"transition": "wf_cancel", "comment": "Budget cut"})
        self.assertEqual(resp.status_code, 302)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.state, CampaignState.CANCELLED)


class WorkflowSeedTest(TestCase):
    def test_seed_twice_and_covers_multiple_states(self):
        from django.core.management import call_command

        call_command("seed")
        count = Campaign.objects.count()
        call_command("seed")
        self.assertEqual(Campaign.objects.count(), count)
        self.assertGreaterEqual(len(set(Campaign.objects.values_list("state", flat=True))), 2)
