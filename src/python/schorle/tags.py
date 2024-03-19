from enum import Enum


class HTMLTag(str, Enum):
    ROOT = "schorle-root"
    PAGE = "schorle-page"
    COMPONENT = "schorle-component"
    PRE = "pre"
    CODE = "code"
    SVG = "svg"
    ICON = "i"
    FIGURE = "figure"
    DEV_FOOTER = "dev-footer"
    FOOTER = "footer"
    HTML = "html"
    HEAD = "head"
    BODY = "body"
    P = "p"
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    H6 = "h6"
    DIV = "div"
    SPAN = "span"
    A = "a"
    IMG = "img"
    UL = "ul"
    OL = "ol"
    LI = "li"
    TABLE = "table"
    TR = "tr"
    TD = "td"
    TH = "th"
    FORM = "form"
    INPUT = "input"
    SELECT = "select"
    OPTION = "option"
    BUTTON = "button"
    SCRIPT = "script"
    STYLE = "style"
    META = "meta"
    LINK = "link"
    TITLE = "title"
