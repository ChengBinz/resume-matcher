from pydantic import BaseModel


class InterviewQuestion(BaseModel):
    id: int
    question: str
    intent: str
    category: str
    reference_answer: str = ""


class InterviewQuestionsRequest(BaseModel):
    resume_text: str
    jd: str


class InterviewQuestionsResponse(BaseModel):
    questions: list[InterviewQuestion]
