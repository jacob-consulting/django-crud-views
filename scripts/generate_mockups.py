"""Generate UI mockup PNGs for django-crud-views documentation."""

from PIL import Image, ImageDraw, ImageFont
import os

# --- Colour palette (Bootstrap 5 inspired) ---
WHITE = "#ffffff"
LIGHT_BG = "#f8f9fa"
DARK_TEXT = "#212529"
MUTED_TEXT = "#6c757d"
PRIMARY = "#0d6efd"
PRIMARY_HOVER = "#0b5ed7"
SECONDARY = "#6c757d"
SUCCESS = "#198754"
DANGER = "#dc3545"
WARNING = "#ffc107"
BORDER = "#dee2e6"
CARD_BORDER = "#ced4da"
TABLE_STRIPE = "#f2f2f2"
LINK_COLOR = "#0d6efd"
HEADER_BG = "#e9ecef"

W = 960
PADDING = 30
INNER_W = W - 2 * PADDING


# Font helpers
def get_fonts():
    """Try to find suitable fonts on the system."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    ]

    def find(paths, size):
        for p in paths:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    return {
        "title": find(bold_paths, 22),
        "heading": find(bold_paths, 17),
        "body": find(font_paths, 14),
        "body_bold": find(bold_paths, 14),
        "small": find(font_paths, 12),
        "small_bold": find(bold_paths, 12),
        "mono": find(mono_paths, 12),
        "icon": find(font_paths, 13),
    }


FONTS = get_fonts()


# --- Drawing primitives ---


def rounded_rect(draw, xy, fill=None, outline=None, radius=6, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_button(draw, x, y, label, color=PRIMARY, text_color=WHITE, outlined=False, small=False):
    font = FONTS["small_bold"] if small else FONTS["body_bold"]
    tw = draw.textlength(label, font=font)
    px, py = (10, 4) if small else (16, 8)
    w = int(tw + 2 * px)
    h = int((FONTS["small"].size if small else FONTS["body"].size) + 2 * py)
    if outlined:
        rounded_rect(draw, (x, y, x + w, y + h), fill=WHITE, outline=color, radius=4, width=2)
        draw.text((x + px, y + py), label, fill=color, font=font)
    else:
        rounded_rect(draw, (x, y, x + w, y + h), fill=color, radius=4)
        draw.text((x + px, y + py), label, fill=text_color, font=font)
    return w, h


def draw_card(draw, x, y, w, h, header_text=None, header_icon=None):
    rounded_rect(draw, (x, y, x + w, y + h), fill=WHITE, outline=CARD_BORDER, radius=6)
    top = y
    if header_text:
        hh = 40
        rounded_rect(draw, (x, y, x + w, y + hh), fill=HEADER_BG, outline=CARD_BORDER, radius=6)
        # Redraw bottom corners as square to join with card body
        draw.rectangle((x + 1, y + hh - 8, x + w - 1, y + hh), fill=HEADER_BG)
        draw.line((x, y + hh, x + w, y + hh), fill=CARD_BORDER)
        text = header_text
        if header_icon:
            text = f"{header_icon}  {header_text}"
        draw.text((x + 14, y + 11), text, fill=DARK_TEXT, font=FONTS["body_bold"])
        top = y + hh
    return top


def draw_table(draw, x, y, col_widths, headers, rows, w=None):
    if w is None:
        w = sum(col_widths)
    row_h = 32
    # Header
    draw.rectangle((x, y, x + w, y + row_h), fill=HEADER_BG)
    draw.line((x, y + row_h, x + w, y + row_h), fill=BORDER)
    cx = x
    for i, hdr in enumerate(headers):
        draw.text((cx + 10, y + 8), hdr, fill=DARK_TEXT, font=FONTS["small_bold"])
        cx += col_widths[i]
    cur_y = y + row_h
    for ri, row in enumerate(rows):
        bg = TABLE_STRIPE if ri % 2 == 1 else WHITE
        draw.rectangle((x, cur_y, x + w, cur_y + row_h), fill=bg)
        draw.line((x, cur_y + row_h, x + w, cur_y + row_h), fill=BORDER)
        cx = x
        for ci, cell in enumerate(row):
            color = DARK_TEXT
            font = FONTS["small"]
            if isinstance(cell, tuple):
                cell, color, font = cell[0], cell[1], cell[2] if len(cell) > 2 else FONTS["small"]
            draw.text((cx + 10, cur_y + 8), str(cell), fill=color, font=font)
            cx += col_widths[ci]
        cur_y += row_h
    # Border
    draw.rectangle((x, y, x + w, cur_y), outline=BORDER)
    return cur_y


def draw_form_field(draw, x, y, label, value="", w=400, required=False):
    label_text = f"{label} *" if required else label
    draw.text((x, y), label_text, fill=DARK_TEXT, font=FONTS["body_bold"])
    fy = y + 22
    fh = 34
    rounded_rect(draw, (x, fy, x + w, fy + fh), fill=WHITE, outline=BORDER, radius=4)
    if value:
        draw.text((x + 10, fy + 8), value, fill=DARK_TEXT, font=FONTS["body"])
    return fy + fh + 12


def draw_breadcrumb(draw, x, y, items):
    cx = x
    for i, item in enumerate(items):
        color = MUTED_TEXT if i < len(items) - 1 else DARK_TEXT
        font = FONTS["small"] if i < len(items) - 1 else FONTS["small_bold"]
        draw.text((cx, y), item, fill=color, font=font)
        cx += draw.textlength(item, font=font) + 4
        if i < len(items) - 1:
            draw.text((cx, y), "/", fill=MUTED_TEXT, font=FONTS["small"])
            cx += draw.textlength("/", font=FONTS["small"]) + 4
    return y + 20


def draw_context_actions(draw, x, y, actions):
    """Draw a Bootstrap 5 button group for context actions."""
    cx = x
    gap = 4
    for label, color, outlined in actions:
        bw, bh = draw_button(draw, cx, y, label, color=color, outlined=outlined)
        cx += bw + gap
    return y + bh + 10


def draw_page_header(draw, y, title, breadcrumbs=None, context_actions=None):
    """Draw page header with title, breadcrumbs, and context action buttons."""
    if breadcrumbs:
        y = draw_breadcrumb(draw, PADDING, y, breadcrumbs)
        y += 4

    draw.text((PADDING, y), title, fill=DARK_TEXT, font=FONTS["title"])
    y += 32

    if context_actions:
        y = draw_context_actions(draw, PADDING, y, context_actions)
        y += 6

    # Divider
    draw.line((PADDING, y, W - PADDING, y), fill=BORDER)
    y += 16
    return y


def create_image(height):
    img = Image.new("RGB", (W, height), LIGHT_BG)
    draw = ImageDraw.Draw(img)
    return img, draw


# --- Mockup generators ---


def mockup_list_view():
    H = 580
    img, draw = create_image(H)

    y = PADDING
    y = draw_page_header(
        draw,
        y,
        "Authors",
        breadcrumbs=["Home", "Authors"],
        context_actions=[
            ("\u2190  Parent", SECONDARY, True),
            ("\u2261  Filter", PRIMARY, True),
            ("+  Create", PRIMARY, True),
        ],
    )

    # Filter card (collapsed state indicator)
    card_y = y
    card_h = 90
    body_y = draw_card(draw, PADDING, card_y, INNER_W, card_h, header_text="Filter", header_icon="\u25bc")
    # Filter fields inside card
    fx = PADDING + 14
    fy = body_y + 10
    draw.text((fx, fy), "First name", fill=MUTED_TEXT, font=FONTS["small"])
    rounded_rect(draw, (fx, fy + 16, fx + 200, fy + 40), fill=WHITE, outline=BORDER, radius=3)
    draw.text((fx + 220, fy), "Last name", fill=MUTED_TEXT, font=FONTS["small"])
    rounded_rect(draw, (fx + 220, fy + 16, fx + 420, fy + 40), fill=WHITE, outline=BORDER, radius=3)

    y = card_y + card_h + 16

    # Table
    cols = [50, 200, 200, 200, INNER_W - 650]
    headers = ["#", "First Name", "Last Name", "Email", "Actions"]
    rows = [
        ["1", "Douglas", "Adams", "d.adams@example.com", ""],
        ["2", "Terry", "Pratchett", "t.pratchett@example.com", ""],
        ["3", "Isaac", "Asimov", "i.asimov@example.com", ""],
        ["4", "Ursula", "Le Guin", "u.leguin@example.com", ""],
        ["5", "Arthur", "Clarke", "a.clarke@example.com", ""],
    ]
    end_y = draw_table(draw, PADDING, y, cols, headers, rows, w=INNER_W)

    # Draw action buttons in last column of each row
    for ri in range(len(rows)):
        row_y = y + 32 + ri * 32  # header height + row offset
        ax = PADDING + sum(cols[:-1]) + 6
        bw, _ = draw_button(draw, ax, row_y + 4, "\u2139", color=PRIMARY, outlined=True, small=True)
        bw2, _ = draw_button(draw, ax + bw + 3, row_y + 4, "\u270e", color=PRIMARY, outlined=True, small=True)
        draw_button(draw, ax + bw + bw2 + 6, row_y + 4, "\u2717", color=DANGER, outlined=True, small=True)

    # Pagination
    py = end_y + 12
    draw.text((PADDING, py), "Showing 1-5 of 12 results", fill=MUTED_TEXT, font=FONTS["small"])
    px = W - PADDING - 200
    for i, (lbl, active) in enumerate([("\u2190", False), ("1", True), ("2", False), ("3", False), ("\u2192", False)]):
        bx = px + i * 38
        if active:
            rounded_rect(draw, (bx, py - 2, bx + 32, py + 24), fill=PRIMARY, radius=4)
            draw.text((bx + 10, py + 2), lbl, fill=WHITE, font=FONTS["small_bold"])
        else:
            rounded_rect(draw, (bx, py - 2, bx + 32, py + 24), fill=WHITE, outline=BORDER, radius=4)
            draw.text((bx + 10, py + 2), lbl, fill=PRIMARY, font=FONTS["small"])

    return img


def mockup_detail_view():
    H = 460
    img, draw = create_image(H)

    y = PADDING
    y = draw_page_header(
        draw,
        y,
        "Author: Douglas Adams",
        breadcrumbs=["Home", "Authors", "Douglas Adams"],
        context_actions=[
            ("\u2190  List", SECONDARY, True),
            ("\u270e  Update", PRIMARY, True),
            ("\u2717  Delete", DANGER, True),
        ],
    )

    # Detail card - split layout
    card_x = PADDING
    card_w = INNER_W
    card_h = 300
    body_y = draw_card(draw, card_x, y, card_w, card_h, header_text="Details")

    # Property rows in a two-column split layout
    props = [
        ("First Name", "Douglas"),
        ("Last Name", "Adams"),
        ("Email", "d.adams@example.com"),
        ("Date of Birth", "March 11, 1952"),
        ("Bio", "English author, best known for The Hitchhiker's Guide..."),
        ("Active", "\u2713  Yes"),
    ]

    py = body_y + 14
    label_w = 160
    for label, value in props:
        # Label on left (muted), value on right
        draw.text((card_x + 16, py), label, fill=MUTED_TEXT, font=FONTS["body_bold"])
        val_color = SUCCESS if value.startswith("\u2713") else DARK_TEXT
        draw.text((card_x + 16 + label_w, py), value, fill=val_color, font=FONTS["body"])
        py += 30
        # Separator line
        draw.line((card_x + 14, py - 6, card_x + card_w - 14, py - 6), fill=BORDER)

    return img


def mockup_create_view():
    H = 500
    img, draw = create_image(H)

    y = PADDING
    y = draw_page_header(
        draw,
        y,
        "Create Author",
        breadcrumbs=["Home", "Authors", "Create"],
        context_actions=[
            ("\u2190  List", SECONDARY, True),
        ],
    )

    # Form card
    card_h = 320
    body_y = draw_card(draw, PADDING, y, INNER_W, card_h)
    fy = body_y + 16

    fw = INNER_W - 60
    fx = PADDING + 20
    fy = draw_form_field(draw, fx, fy, "First Name", required=True, w=fw)
    fy = draw_form_field(draw, fx, fy, "Last Name", required=True, w=fw)
    fy = draw_form_field(draw, fx, fy, "Email", w=fw)
    fy = draw_form_field(draw, fx, fy, "Bio", w=fw)

    # Buttons
    by = fy + 8
    bw, bh = draw_button(draw, fx, by, "  Save  ", color=SUCCESS)
    draw_button(draw, fx + bw + 10, by, "  Cancel  ", color=SECONDARY, outlined=True)

    return img


def mockup_update_view():
    H = 500
    img, draw = create_image(H)

    y = PADDING
    y = draw_page_header(
        draw,
        y,
        "Update Author: Douglas Adams",
        breadcrumbs=["Home", "Authors", "Douglas Adams", "Update"],
        context_actions=[
            ("\u2190  List", SECONDARY, True),
        ],
    )

    # Form card
    card_h = 320
    body_y = draw_card(draw, PADDING, y, INNER_W, card_h)
    fy = body_y + 16

    fw = INNER_W - 60
    fx = PADDING + 20
    fy = draw_form_field(draw, fx, fy, "First Name", value="Douglas", required=True, w=fw)
    fy = draw_form_field(draw, fx, fy, "Last Name", value="Adams", required=True, w=fw)
    fy = draw_form_field(draw, fx, fy, "Email", value="d.adams@example.com", w=fw)
    fy = draw_form_field(draw, fx, fy, "Bio", value="English author, best known for...", w=fw)

    # Buttons
    by = fy + 8
    bw, bh = draw_button(draw, fx, by, "  Save  ", color=SUCCESS)
    draw_button(draw, fx + bw + 10, by, "  Cancel  ", color=SECONDARY, outlined=True)

    return img


def mockup_delete_view():
    H = 340
    img, draw = create_image(H)

    y = PADDING
    y = draw_page_header(
        draw,
        y,
        "Delete Author: Douglas Adams",
        breadcrumbs=["Home", "Authors", "Douglas Adams", "Delete"],
        context_actions=[
            ("\u2190  List", SECONDARY, True),
        ],
    )

    # Warning card
    card_h = 170
    body_y = draw_card(draw, PADDING, y, INNER_W, card_h)

    # Warning message
    wy = body_y + 20
    draw.text(
        (PADDING + 20, wy), "\u26a0  Are you sure you want to delete this author?", fill=DANGER, font=FONTS["heading"]
    )
    wy += 34

    # Object summary
    draw.text((PADDING + 20, wy), "Author:", fill=MUTED_TEXT, font=FONTS["body_bold"])
    draw.text((PADDING + 90, wy), "Douglas Adams", fill=DARK_TEXT, font=FONTS["body"])
    wy += 26
    draw.text((PADDING + 20, wy), "This action cannot be undone.", fill=MUTED_TEXT, font=FONTS["small"])

    # Buttons
    by = wy + 30
    bw, bh = draw_button(draw, PADDING + 20, by, "  Confirm Delete  ", color=DANGER)
    draw_button(draw, PADDING + 20 + bw + 10, by, "  Cancel  ", color=SECONDARY, outlined=True)

    return img


def mockup_manage_view():
    H = 580
    img, draw = create_image(H)

    y = PADDING
    y = draw_page_header(
        draw,
        y,
        "Manage: Author ViewSet",
        breadcrumbs=["Home", "Authors", "Manage"],
        context_actions=[
            ("\u2190  List", SECONDARY, True),
        ],
    )

    # Properties table
    draw.text((PADDING, y), "ViewSet Properties", fill=DARK_TEXT, font=FONTS["heading"])
    y += 26
    cols = [200, INNER_W - 200]
    props = [
        ["name", "author"],
        ["prefix", "app"],
        ["model", "app.Author"],
        ["pk", "INT"],
        ["pk_name", "pk"],
    ]
    y = draw_table(draw, PADDING, y, cols, ["Property", "Value"], props, w=INNER_W)
    y += 20

    # Permissions table
    draw.text((PADDING, y), "Permissions", fill=DARK_TEXT, font=FONTS["heading"])
    y += 26
    pcols = [200, 300, INNER_W - 500]
    perms = [
        ["view", "app.view_author", ("\u2713 Granted", SUCCESS)],
        ["add", "app.add_author", ("\u2713 Granted", SUCCESS)],
        ["change", "app.change_author", ("\u2713 Granted", SUCCESS)],
        ["delete", "app.delete_author", ("\u2713 Granted", SUCCESS)],
    ]
    y = draw_table(draw, PADDING, y, pcols, ["Permission", "Django Permission", "Access"], perms, w=INNER_W)

    return img


# --- Main ---


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "img")
    os.makedirs(out_dir, exist_ok=True)

    mockups = {
        "view_list": mockup_list_view,
        "view_detail": mockup_detail_view,
        "view_create": mockup_create_view,
        "view_update": mockup_update_view,
        "view_delete": mockup_delete_view,
        "view_manage": mockup_manage_view,
    }

    for name, func in mockups.items():
        path = os.path.join(out_dir, f"{name}.png")
        img = func()
        img.save(path, "PNG", optimize=True)
        print(f"  {path}")

    print(f"\nGenerated {len(mockups)} mockups in {out_dir}/")


if __name__ == "__main__":
    main()
