from pydantic import BaseModel


class IngestResponse(BaseModel):
    accepted: int
