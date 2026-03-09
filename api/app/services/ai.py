import json
from openai import AsyncOpenAI
from app.core.config import settings


class AIService:
    """AI analysis service using OpenAI with file upload"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def analyze_report_with_file(
        self, 
        file_path: str,
        file_type: str,
        questionnaire_data: dict = None
    ) -> dict:
        """
        Upload file directly to OpenAI and get analysis
        
        Args:
            file_path: Local file path
            file_type: pdf, jpg, or png
            questionnaire_data: User lifestyle data
        
        Returns:
            dict with summary, abnormal_items, normal_items, lifestyle_advice
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(questionnaire_data)
        
        # Upload file to OpenAI
        with open(file_path, "rb") as f:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o for file understanding
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional health report analyst. 
Analyze the uploaded health checkup report and provide insights in JSON format.

Output MUST be valid JSON with this exact structure:
{
  "summary": "Brief overview of health status (2-3 sentences)",
  "abnormal_items": ["item 1", "item 2", ...],
  "normal_items": ["item 1", "item 2", ...],
  "lifestyle_advice": "Actionable recommendations (1-2 sentences)"
}

Focus on:
- Blood test results (血糖, 血脂, 肝功能, 肾功能)
- Physical examination results
- Imaging findings (超声, X光, CT)
- Any values outside normal range
"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": "upload://file"}
                            } if file_type in ["jpg", "png"] else None
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        
        # For PDF, we need to use file upload
        if file_type == "pdf":
            # Upload file to OpenAI
            uploaded_file = await self.client.files.create(
                file=open(file_path, "rb"),
                purpose="vision"
            )
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional health report analyst. 
Analyze the uploaded health checkup report and provide insights in JSON format.

Output MUST be valid JSON with this exact structure:
{
  "summary": "Brief overview of health status (2-3 sentences)",
  "abnormal_items": ["item 1", "item 2", ...],
  "normal_items": ["item 1", "item 2", ...],
  "lifestyle_advice": "Actionable recommendations (1-2 sentences)"
}

Focus on:
- Blood test results (血糖, 血脂, 肝功能, 肾功能)
- Physical examination results
- Imaging findings (超声, X光, CT)
- Any values outside normal range
"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"file://{uploaded_file.id}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        
        # Parse JSON response
        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            return {
                "summary": response.choices[0].message.content,
                "abnormal_items": [],
                "normal_items": [],
                "lifestyle_advice": ""
            }
    
    async def analyze_image_report(
        self,
        image_data: bytes,
        questionnaire_data: dict = None
    ) -> dict:
        """
        Analyze image-based report (JPG/PNG)
        """
        import base64
        
        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode("utf-8")
        
        prompt = self._build_analysis_prompt(questionnaire_data)
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional health report analyst. 
Analyze the uploaded health checkup report image and provide insights in JSON format.

Output MUST be valid JSON with this exact structure:
{
  "summary": "Brief overview of health status (2-3 sentences)",
  "abnormal_items": ["item 1", "item 2", ...],
  "normal_items": ["item 1", "item 2", ...],
  "lifestyle_advice": "Actionable recommendations (1-2 sentences)"
}

Focus on:
- Blood test results
- Physical examination results
- Any values outside normal range
"""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            return {
                "summary": response.choices[0].message.content,
                "abnormal_items": [],
                "normal_items": [],
                "lifestyle_advice": ""
            }
    
    async def answer_question(
        self, 
        report_text: str, 
        analysis_result: str,
        question: str
    ) -> str:
        """
        Answer follow-up questions about the report
        """
        context = f"""
Health Report Summary:
{analysis_result}

Original Report:
{report_text[:3000] if report_text else 'No report text available'}
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional health consultant. "
                              "Answer the user's question based on their health report. "
                              "If the question is outside your expertise, recommend consulting a doctor."
                },
                {
                    "role": "user",
                    "content": f"{context}\n\nUser Question: {question}"
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def _build_analysis_prompt(self, questionnaire_data: dict = None) -> str:
        """Build analysis prompt with questionnaire data"""
        prompt = "Please analyze this health checkup report and provide insights."
        
        if questionnaire_data:
            prompt += "\n\nUser Lifestyle Information:\n"
            
            # Map common fields
            field_map = {
                "smoking": "吸烟情况",
                "alcohol": "饮酒情况",
                "late_sleep": "睡眠时间",
                "medical_history": "病史",
                "exercise_frequency": "运动频率",
                "diet_preference": "饮食习惯"
            }
            
            for eng, cn in field_map.items():
                if eng in questionnaire_data and questionnaire_data[eng]:
                    prompt += f"- {cn}: {questionnaire_data[eng]}\n"
        
        return prompt


# Singleton instance
ai_service = AIService()
