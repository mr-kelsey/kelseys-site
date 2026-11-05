from dataclasses import dataclass


@dataclass
class Project:
    id: int = None
    slug: str = ""
    title: str = ""
    description: str = ""
    body: str = ""
    url: str = ""
    report_pdf: str = ""
    created_at: str = ""


@dataclass
class Post:
    id: int = None
    slug: str = ""
    title: str = ""
    body: str = ""
    created_at: str = ""


@dataclass
class ContactMessage:
    id: int = None
    name: str = ""
    email: str = ""
    message: str = ""
    created_at: str = ""
