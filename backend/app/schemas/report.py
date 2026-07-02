"""Report Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel


class ReportSummary(BaseModel):
    id: str
    type: str
    date_range_start: date
    date_range_end: date
    file_path: str
    paper_count: int
    repo_count: int
    delivery_status: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class ReportDetail(ReportSummary):
    content: str
