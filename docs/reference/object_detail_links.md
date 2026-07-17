# Links

Make a property value a clickable link using `LinkConfig` or a URL name string shorthand:

```python
from crud_views_object_detail.lib import x, LinkConfig

"properties": [
    # String shorthand — reverses URL with the related object's pk
    x("author", link="author-detail"),

    # Explicit args
    x("author", link=LinkConfig(url="author-detail", args=["pk"])),

    # Explicit kwargs
    x("author", link=LinkConfig(url="author-detail", kwargs={"slug": "slug"})),
]
```

The `args` and `kwargs` values are attribute names looked up on the resolved value.
