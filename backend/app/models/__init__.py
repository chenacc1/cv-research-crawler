from app.models.paper import Paper
from app.models.author import Author, PaperAuthor
from app.models.category import Category, PaperCategory
from app.models.repo import GitHubRepo
from app.models.tag import UserTag, PaperTag, RepoTag
from app.models.crawl_log import CrawlLog
from app.models.report import Report

__all__ = [
    "Paper",
    "Author",
    "PaperAuthor",
    "Category",
    "PaperCategory",
    "GitHubRepo",
    "UserTag",
    "PaperTag",
    "RepoTag",
    "CrawlLog",
    "Report",
]
