from typing import List

from lxml import html
from lxml.html import Element


class Header:

    def __init__(self, element: Element):
        self.element = element

    @property
    def text(self) -> bool:
        return self.element.text_content().strip()

    @property
    def orderable(self) -> bool:
        return "orderable" in self.element.classes

    @property
    def is_action(self) -> bool:
        return self.text == "Actions"

    @property
    def link(self):
        if self.is_action:
            return None

    @property
    def actions(self):
        if self.is_action:
            for index, element in self.element.xpath("a"):
                yield Action(index, element)


class Action:
    def __init__(self, index: int, element: Element):
        self.index = index
        self.element = element

    def __str__(self):
        try:
            key = self.key
        except:
            key = "KEY-ERROR"
        return f"action({key}:{self.index}:{self.text})"

    @property
    def is_disabled(self) -> bool:
        if self.element.tag == "span":
            return "disabled" in self.element.xpath("a")[0].classes
        return "disabled" in self.element.classes

    @property
    def text(self) -> str:
        return self.element.text_content().strip()

    @property
    def title(self) -> str:
        """
        Get the title either from span or from a tag
        """
        return self.element.attrib["title"].strip()

    @property
    def key(self) -> str | None:
        if self.element.tag == "span":
            return self.element.xpath("a")[0].attrib.get("cv-key", None)
        return self.element.attrib.get("cv-key", None)

    @property
    def href(self) -> str | None:
        # disabled buttons have no href
        if self.element.tag == "span":
            return self.element.xpath("a")[0].attrib.get("href")
        # context actions do not have a span when disabled
        return self.element.attrib.get("href")


class Column:

    def __init__(self, index: int, row: "Row", element: Element, action_index: int):
        self.index = index
        self.row = row
        self.element = element
        self.action_index = action_index

    def __str__(self):
        return f"col({self.row.index},{self.index}:{self.text})"

    @property
    def text(self) -> bool:
        return self.element.text_content().strip()

    @property
    def actions(self) -> List[Action]:
        assert self.index == self.action_index
        data: List[Action] = []
        for index, element in enumerate(self.element.xpath("div/a|span")):
            action = Action(index, element)
            data.append(action)
        return data


class Row:
    def __init__(self, index: int, element: Element, action_index: int):
        self.index = index
        self.element = element
        self.action_index = action_index

    def __str__(self):
        return f"row({self.index})"

    @property
    def columns(self) -> List[Column]:
        result = []
        for index, element in enumerate(self.element.xpath("td")):
            column = Column(index, self, element, action_index=self.action_index)
            result.append(column)
        return result

    @property
    def actions(self) -> List[Action]:
        column = self.columns[self.action_index]
        return column.actions

    def get_action(self, key: str) -> Action:
        for action in self.actions:
            if action.key == key:
                return action
        raise KeyError(key)


class Table:

    def __init__(self, response):
        self.content = response.content.decode("utf-8").strip()
        self.html = html.fromstring(self.content)

    @property
    def context(self) -> Element:
        return self.html.xpath("//div[@cv-context-container='true']")[0]

    @property
    def context_actions(self) -> List[Action]:
        return [Action(index=index, element=element) for index, element in enumerate(self.context.xpath("a"))]

    def get_context_action(self, key: str) -> Action:
        for action in self.context_actions:
            if action.key == key:
                return action
        raise KeyError(key)

    @property
    def table(self):
        return self.html.xpath("//table")[0]

    @property
    def tbody(self):
        return self.table.xpath("//tbody")[0]

    @property
    def rows(self) -> List[Row]:
        action_index = self.action_index
        return [Row(index, row, action_index=action_index) for index, row in enumerate(self.tbody.xpath("tr"))]

    @property
    def thead(self):
        return self.table.xpath("//thead")[0]

    @property
    def headers(self) -> List[Header]:
        return [Header(header) for header in self.thead.xpath("//th")]

    @property
    def action_index(self) -> int | None:
        for index, header in enumerate(self.headers):
            if header.is_action:
                return index
