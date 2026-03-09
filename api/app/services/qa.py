import json
from openai import AsyncOpenAI
from app.core.config import settings


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
        questionnaire_data: str = None
    ) -> dict:
        """
        Answer user's follow-up question about the health report
        
        Args:
            question: User's question
            analysis_result: JSON string from AI analysis
            questionnaire_data: User lifestyle information
        
        Returns:
            dict with answer
        """
        # Build context
        context = self._build_context(analysis_result, questionnaire_data)
        
        # Build prompt
        prompt = f"""
Based on the health report analysis and user's lifestyle information:

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
                              "Answer user questions based on their health report."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer
        }
    
    def _build_context(
        self,
        analysis_result: str,
        questionnaire_data: str = None
    ) -> str:
        """Build context from analysis and questionnaire"""
        context = []
        
        # Parse analysis result
        if analysis_result:
            try:
                if isinstance(analysis_result, str):
                    data = json.loads(analysis_result)
                else:
                    data = analysis_result
                
                if "summary" in data:
                    context.append(f"体检总结: {data['summary']}")
                
                if "abnormal_items" in data and data["abnormal_items"]:
                    abnormal = ", ".join(data["abnormal_items"])
                    context.append(f"异常项目: {abnormal}")
                
                if "normal_items" in data and data["normal_items"]:
                    normal = ", ".join(data["normal_items"][:5])  # Limit to 5
                    context.append(f"正常项目: {normal}")
                
                if "lifestyle_advice" in data and data["lifestyle_advice"]:
                    context.append(f"生活建议: {data['lifestyle_advice']}")
                    
            except (json.JSONDecodeError, AttributeError):
                context.append(f"体检分析: {analysis_result}")
        
        # Add lifestyle info
        if questionnaire_data:
            try:
                if isinstance(questionnaire_data, str):
                    lifestyle = json.loads(questionnaire_data)
                else:
                    lifestyle = questionnaire_data
                
                if lifestyle:
                    context.append(f"生活习惯: {json.dumps(lifestyle, ensure_ascii=False)}")
            except:
                pass
        
        return "\n\n".join(context)
    
    async def check_question_limit(self, db, report_id: int) -> dict:
        """
        Check if user can still ask questions
        
        Returns:
            dict with can_ask (bool), remaining (int), message (str)
        """
        from sqlalchemy import select
        from app.models import Report
        
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            return {
                "can_ask": False,
                "remaining": 0,
                "message": "Report not found"
            }
        
        if report.question_count >= self.MAX_QUESTIONS:
            return {
                "can_ask": False,
                "remaining": 0,
                "message": "You have reached the maximum of 2 follow-up questions"
            }
        
        remaining = self.MAX_QUESTIONS - report.question_count
        return {
            "can_ask": True,
            "remaining": remaining,
            "message": f"You have {remaining} question(s) remaining"
        }
    
    async def increment_question_count(self, db, report_id: int):
        """Increment the question count for a report"""
        from sqlalchemy import select
        from app.models import Report
        
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if report:
            report.question_count += 1
            if report.question_count >= self.MAX_QUESTIONS:
                report.qa_active = 0  # Disable further questions


# Singleton instance
qa_service = QAService()
