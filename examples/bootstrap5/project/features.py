"""Registry of example feature apps. Each app task appends exactly one entry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    app: str  # python package name of the example app, e.g. "library"
    title: str  # card/nav title on the home page
    description: str  # one-liner on the home page card
    url_name: str  # URL name of the app's landing page, e.g. "author-list"
    icon: str  # font-awesome classes


FEATURES: list[Feature] = [
    # example feature apps append their entry here
]
