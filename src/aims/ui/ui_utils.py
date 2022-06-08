blank_date_edit_style = """
selection-color: rgb(0, 0, 0);
selection-background-color: rgb(255, 255, 255)
"""


def highlight(widget):
    widget.setStyleSheet("background-color: rgb(170, 255, 127)")


def unHighlight(widget):
    widget.setStyleSheet("")


def unHighlightDate(widget):
    widget.setStyleSheet(blank_date_edit_style)
