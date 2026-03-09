import json
from typing import Any, List, Optional

from openai import AsyncOpenAI
from sqlalchemy import func, select

from app.core.config import settings
from app.models import QAHistory, Report


class QAService:
    """Question answering service for health report follow-up questions"""

    MAX_QUESTIONS = 2  # Maximum 2 follow-up questions

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def answer_question(
        self,
        question: str,
        analysis_result: str,
        questionnaire_data: str = None,
        qa_history: Optional[List[QAHistory]] = None,
    ) -> dict:
        """
        Answer user's follow-up question about the health report.
        Context includes report summary, questionnaire data and QA history.
        """
        context = self._build_context(analysis_result, questionnaire_data, qa_history)

        prompt = f"""
Based on the health report analysis, user's lifestyle information, and previous follow-up history:

{context}

User's Question: {question}

Please answer the user's question based on the health report.
- Be specific and actionable
- If the question is outside your expertise, recommend consulting a doctor
- Keep the answer concise (2-3 sentences)
- Use friendly, professional tone
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional health consultant. "
                    "Answer user questions based on their health report.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        return {"answer": response.choices[0].message.content}

    def _build_context(
        self,
        analysis_result: str,
        questionnaire_data: str = None,
        qa_history: Optional[List[QAHistory]] = None,
    ) -> str:
        """Build context from analysis, questionnaire and history."""
        context: List[str] = []

        if analysis_result:
            try:
                data = json.loads(analysis_result) if isinstance(analysis_result, str) else analysis_result

                if "summary" in data:
                    context.append(f"体检总结: {data['summary']}")

                if "abnormal_items" in data and data["abnormal_items"]:
                    context.append(f"异常项目: {', '.join(data['abnormal_items'])}")

                if "normal_items" in data and data["normal_items"]:
                    context.append(f"正常项目: {', '.join(data['normal_items'][:5])}")

                if "lifestyle_advice" in data and data["lifestyle_advice"]:
                    context.append(f"生活建议: {data['lifestyle_advice']}")
            except (json.JSONDecodeError, AttributeError):
                context.append(f"体检分析: {analysis_result}")

        if questionnaire_data:
            try:
                lifestyle = json.loads(questionnaire_data) if isinstance(questionnaire_data, str) else questionnaire_data
                if lifestyle:
                    context.append(f"生活习惯: {json.dumps(lifestyle, ensure_ascii=False)}")
            except Exception:
                pass

        if qa_history:
            history_lines = []
            for item in qa_history:
                history_lines.append(f"Q: {item.question}\nA: {item.answer}")
            if history_lines:
                context.append("历史追问:\n" + "\n\n".join(history_lines))

        return "\n\n".join(context)

    async def count_questions(self, db, report_id: int) -> int:
        """Count persisted QA history records for a report."""
        result = await db.execute(
            select(func.count(QAHistory.id)).where(QAHistory.report_id == report_id)
        )
        return int(result.scalar() or 0)

    async def get_qa_history(self, db, report_id: int) -> List[QAHistory]:
        """Get follow-up history in chronological order."""
        result = await db.execute(
            select(QAHistory)
            .where(QAHistory.report_id == report_id)
            .order_by(QAHistory.created_at.asc(), QAHistory.id.asc())
        )
        return result.scalars().all()

    async def check_question_limit(self, db, report_id: int) -> dict[str, Any]:
        """Check if report can still ask questions; source of truth is qa_history count."""
        report_result = await db.execute(select(Report).where(Report.id == report_id))
        report = report_result.scalar_one_or_none()

        if not report:
            return {"can_ask": False, "remaining": 0, "message": "Report not found", "count": 0}

        count = await self.count_questions(db, report_id)
        if count >= self.MAX_QUESTIONS:
            return {
                "can_ask": False,
                "remaining": 0,
                "message": "You have reached the maximum of 2 follow-up questions",
                "count": count,
            }

        remaining = self.MAX_QUESTIONS - count
        return {
            "can_ask": True,
            "remaining": remaining,
            "message": f"You have {remaining} question(s) remaining",
            "count": count,
        }

    async def sync_question_count(self, db, report: Report) -> None:
        """Sync denormalized report.question_count/qa_active from qa_history count."""
        count = await self.count_questions(db, report.id)
        report.question_count = count
        report.qa_active = 1 if count < self.MAX_QUESTIONS else 0


qa_service = QAService()
