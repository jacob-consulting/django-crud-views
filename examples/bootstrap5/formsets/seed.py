from django.contrib.auth import get_user_model

from formsets.models import Choice, Question, Questionnaire
from project.seeding import grant_model_perms

QUESTIONNAIRES = {
    "Customer Survey": {
        "How satisfied are you?": ["Very", "Somewhat", "Not at all"],
        "Would you recommend us?": ["Yes", "No"],
    },
    "Onboarding Feedback": {
        "How was your first week?": ["Great", "Okay", "Rough"],
    },
}


def seed():
    User = get_user_model()
    for username in ("alice", "bob"):
        user = User.objects.get(username=username)
        for model in (Questionnaire, Question, Choice):
            grant_model_perms(user, model)
    for title, questions in QUESTIONNAIRES.items():
        questionnaire, _ = Questionnaire.objects.get_or_create(title=title)
        for text, labels in questions.items():
            question, _ = Question.objects.get_or_create(questionnaire=questionnaire, text=text)
            for label in labels:
                Choice.objects.get_or_create(question=question, label=label)
