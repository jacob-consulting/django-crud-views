# Tutorial - Part 2

Now let's add some other views.


## The Create View

```python
from crispy_forms.layout import Row
from crud_views.lib.views import CreateViewPermissionRequired, MessageMixin
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm

class AuthorCreateForm(CrispyModelForm):

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))

    
class AuthorCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    model = Author
    form_class = AuthorCreateForm
    vs = vs_author
```

Now you see the create button on the list view.

![list-create.png](assets/list-create.png)

Click the create button and you will see the create view.

![create.png](assets/create.png)

After you have created an author you will see the list view again.

![list-create-author.png](assets/list-create-author.png)

> **Note:** You see the message `Created Author Alexander Jacob` because the `MessageMixin` is used.
