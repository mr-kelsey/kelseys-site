from fastlite import database

from app.config import SiteConfig
from app.models import ContactMessage, Post, Project


class Database:
    """Opens a fastlite connection at `db_path` and bootstraps the site's tables."""

    def __init__(self, db_path: str) -> None:
        self.connection = database(db_path)
        self.projects = self.connection.create(
            Project, name="projects", pk="id", transform=True
        )
        self.posts = self.connection.create(Post, name="posts", pk="id", transform=True)
        self.contact_messages = self.connection.create(
            ContactMessage, name="contact_messages", pk="id", transform=True
        )


site_db = Database(SiteConfig().db_path)
