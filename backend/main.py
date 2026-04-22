import asyncio
import json
import traceback

from fastapi import FastAPI, UploadFile, File, Form, Body, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from schemas.resume import ResumeResult, MatchResponse
from schemas.interview import InterviewQuestionsRequest, InterviewQuestionsResponse
from services.pdf_parser import extract_text_from_pdf, extract_candidate_name
from services.archive_parser import is_archive, extract_pdfs_from_archive
from services.llm_service import evaluate_resume, generate_interview_questions, stream_interview_questions

app = FastAPI(title="Resume Matcher API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_single_pdf(filename: str, pdf_bytes: bytes) -> dict:
    """解析单个 PDF 文件字节流，返回解析结果"""
    if len(pdf_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        return {"filename": filename, "candidate_name": None, "text": None, "error": "文件大小超过限制"}
    try:
        text = extract_text_from_pdf(pdf_bytes)
        if not text.strip():
            return {"filename": filename, "candidate_name": None, "text": None, "error": "PDF 内容为空或无法提取文本"}
        candidate_name = extract_candidate_name(filename, text)
        return {"filename": filename, "candidate_name": candidate_name, "text": text, "error": None}
    except Exception as e:
        return {"filename": filename, "candidate_name": None, "text": None, "error": f"PDF 解析失败: {e}"}


@app.post("/api/match", response_model=MatchResponse)
async def match_resumes(
    files: list[UploadFile] = File(..., description="PDF 简历文件或压缩包"),
    jd: str = Form(..., description="岗位描述（JD）"),
):
    """上传简历并与 JD 进行匹配评估，支持 PDF 和压缩包（zip/tar.gz）"""
    # 解析所有文件（PDF 直接解析，压缩包提取其中的 PDF）
    parsed_resumes = []
    for f in files:
        raw = await f.read()
        fname = f.filename.lower()

        if fname.endswith(".pdf"):
            parsed_resumes.append(_parse_single_pdf(f.filename, raw))

        elif is_archive(f.filename):
            try:
                pdf_entries = extract_pdfs_from_archive(raw, f.filename)
                if not pdf_entries:
                    parsed_resumes.append(
                        {"filename": f.filename, "candidate_name": None, "text": None, "error": "压缩包中未找到 PDF 文件"}
                    )
                else:
                    for entry in pdf_entries:
                        parsed_resumes.append(
                            _parse_single_pdf(entry["filename"], entry["content"])
                        )
            except Exception as e:
                parsed_resumes.append(
                    {"filename": f.filename, "candidate_name": None, "text": None, "error": f"压缩包解析失败: {e}"}
                )
        else:
            parsed_resumes.append(
                {"filename": f.filename, "candidate_name": None, "text": None, "error": "不支持的文件格式，仅支持 PDF 和压缩包"}
            )

    if len(parsed_resumes) > settings.MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"解析后简历总数为 {len(parsed_resumes)} 份，超过上限 {settings.MAX_UPLOAD_FILES} 份",
        )

    # 并发调用 LLM 评估
    async def evaluate_one(resume_info: dict) -> ResumeResult:
        if resume_info["error"]:
            return ResumeResult(
                filename=resume_info["filename"],
                candidate_name=resume_info.get("candidate_name"),
                overall_score=0,
                skill_score=0,
                experience_score=0,
                education_score=0,
                soft_skill_score=0,
                strengths=[],
                weaknesses=[],
                summary="",
                error=resume_info["error"],
            )
        try:
            result = await evaluate_resume(resume_info["text"], jd)
            return ResumeResult(
                filename=resume_info["filename"],
                candidate_name=resume_info.get("candidate_name"),
                overall_score=result.get("overall_score", 0),
                skill_score=result.get("skill_score", 0),
                experience_score=result.get("experience_score", 0),
                education_score=result.get("education_score", 0),
                soft_skill_score=result.get("soft_skill_score", 0),
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                summary=result.get("summary", ""),
                resume_text=resume_info["text"],
            )
        except Exception as e:
            traceback.print_exc()
            return ResumeResult(
                filename=resume_info["filename"],
                candidate_name=resume_info.get("candidate_name"),
                overall_score=0,
                skill_score=0,
                experience_score=0,
                education_score=0,
                soft_skill_score=0,
                strengths=[],
                weaknesses=[],
                summary="",
                error=f"LLM 评估失败: {e}",
            )

    tasks = [evaluate_one(r) for r in parsed_resumes]
    results = await asyncio.gather(*tasks)

    # 按 overall_score 降序排序
    results_sorted = sorted(results, key=lambda x: x.overall_score, reverse=True)

    return MatchResponse(results=results_sorted, total=len(results_sorted))


@app.post("/api/interview-questions", response_model=InterviewQuestionsResponse)
async def get_interview_questions(
    request: InterviewQuestionsRequest = Body(...),
):
    """根据简历内容生成面试问题"""
    try:
        result = await generate_interview_questions(request.resume_text, request.jd)
        return InterviewQuestionsResponse(
            questions=result.get("questions", [])
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成面试问题失败: {e}")


@app.post("/api/interview-questions-stream")
async def stream_interview_questions_endpoint(
    request: InterviewQuestionsRequest = Body(...),
):
    """流式生成面试问题，通过 SSE 逐个返回问题"""

    async def event_generator():
        try:
            async for question in stream_interview_questions(request.resume_text, request.jd):
                data = json.dumps(question, ensure_ascii=False)
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            traceback.print_exc()
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
