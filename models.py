from pydantic import BaseModel


class Question(BaseModel):
    question: str
    session_id: str | None = None
    n_results: int = 3
    temperature: float = 0.3
    top_k: int = 40


class ResetRequest(BaseModel):
    session_id: str


class DeleteRequest(BaseModel):
    filename: str


class URLingest(BaseModel):
    url: str
