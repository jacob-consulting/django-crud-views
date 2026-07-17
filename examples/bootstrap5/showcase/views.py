from crispy_forms.layout import Fieldset, Row

from crud_views.lib.crispy import (
    Column2,
    Column4,
    Column6,
    Column12,
    CrispyDeleteForm,
    CrispyModelForm,
    CrispyViewMixin,
)
from crud_views.lib.view import CardAction
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    CardListViewPermissionRequired,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet

from showcase.models import Recipe

cv_recipe = ViewSet(model=Recipe, name="recipe", icon_header="fa-solid fa-utensils")


class RecipeForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Recipe
        fields = ["title", "difficulty", "servings", "description"]

    def get_layout_fields(self):
        # crispy Fieldsets group the form into titled sections
        return [
            Fieldset("Basics", Row(Column6("title"), Column4("difficulty"), Column2("servings"))),
            Fieldset("Details", Row(Column12("description"))),
        ]


class RecipeCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_recipe
    cv_path = ""  # the card list IS the landing page of this ViewSet
    cv_card_container_class = "col-md-6"
    cv_context_actions = ["card", "create"]
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="favorite", label="Favorite"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]


class RecipeDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_recipe
    cv_context_actions = ["card", "update", "delete"]
    cv_property_display = [
        {
            "title": "Basics",
            "icon": "utensils",
            "description": "What and how much",
            "properties": ["title", "difficulty", "servings", "favorite"],
        },
        {
            "title": "Details",
            "icon": "circle-info",
            "description": "Preparation and metadata",
            "properties": [
                "description",
                "created_dt",
                {"path": "summary", "detail": "Computed on the view"},
            ],
        },
    ]

    def summary(self, instance):
        return f"{instance.title} — {instance.get_difficulty_display()}, serves {instance.servings}"


class RecipeCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_recipe
    cv_context_actions = ["card"]
    form_class = RecipeForm
    cv_message = "Created recipe »{object}«"


class RecipeUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_recipe
    cv_context_actions = ["card"]
    form_class = RecipeForm
    cv_message = "Updated recipe »{object}«"


class RecipeDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_recipe
    cv_context_actions = ["card"]
    form_class = CrispyDeleteForm
    cv_message = "Deleted recipe »{object}«"
    cv_modal = True


class RecipeFavoriteView(MessageMixin, ActionViewPermissionRequired):
    cv_viewset = cv_recipe
    cv_key = "favorite"
    cv_path = "favorite"
    cv_permission = "change"
    cv_icon_action = "fa-regular fa-star"
    cv_action_label_template_code = "Favorite"
    cv_action_short_label_template_code = "Favorite"
    cv_message_template_code = "Toggled favorite for »{{ object }}«"
    cv_message_template_error_code = "Could not toggle favorite for »{{ object }}«"

    def action(self, context) -> bool:
        self.object.favorite = not self.object.favorite
        self.object.save()
        return True
