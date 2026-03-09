import os
import json
from openai import AsyncOpenAI
from app.core.config import settings


class TTSService:
    """Text-to-Speech service using OpenAI TTS"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.voice = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
        self.model = "tts-1"  # tts-1 or tts-1-hd
    
    async def generate_tts(
        self,
        text: str,
        output_filename: str = None
    ) -> dict:
        """
        Convert text to speech and save as MP3
        
        Args:
            text: Text to convert to speech
            output_filename: Optional custom filename
        
        Returns:
            dict with audio_url and file_path
        """
        # Generate filename if not provided
        if not output_filename:
            import uuid
            timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"tts_{timestamp}_{uuid.uuid4().hex[:6]}.mp3"
        
        # Ensure audio directory exists
        audio_dir = os.path.join(settings.UPLOAD_DIR, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        file_path = os.path.join(audio_dir, output_filename)
        
        # Generate speech
        response = await self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3"
        )
        
        # Save to file
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        # Return URL
        audio_url = f"/uploads/audio/{output_filename}"
        
        return {
            "audio_url": audio_url,
            "file_path": file_path,
            "filename": output_filename
        }
    
    async def generate_health_summary_tts(
        self,
        analysis_result: str,
        lifestyle_advice: str = None
    ) -> dict:
        """
        Generate TTS for health summary and lifestyle advice
        
        Args:
            analysis_result: Health summary from AI analysis
            lifestyle_advice: Lifestyle recommendations
        
        Returns:
            dict with audio_url and metadata
        """
        # Build text content
        text_parts = []
        
        # Add summary
        text_parts.append("您好，这是您的体检报告解读。")
        
        if analysis_result:
            # Parse if JSON
            try:
                if isinstance(analysis_result, str):
                    data = json.loads(analysis_result)
                else:
                    data = analysis_result
                
                if "summary" in data:
                    text_parts.append(f"总体情况：{data['summary']}")
                
                if "abnormal_items" in data and data["abnormal_items"]:
                    text_parts.append("需要注意的项目有：")
                    for item in data["abnormal_items"][:5]:  # Limit to 5 items
                        text_parts.append(f"• {item}")
                
                if "lifestyle_advice" in data and data["lifestyle_advice"]:
                    text_parts.append(f"生活建议：{data['lifestyle_advice']}")
                    
            except (json.JSONDecodeError, AttributeError):
                # If not JSON, use as-is
                text_parts.append(f"体检总结：{analysis_result}")
        
        # Add lifestyle advice
        if lifestyle_advice:
            text_parts.append(f"生活建议：{lifestyle_advice}")
        
        # Combine text
        full_text = " ".join(text_parts)
        
        # Limit text length (TTS has limits)
        max_chars = 4000
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "..."
        
        # Generate TTS
        return await self.generate_tts(full_text)
    
    async def generate_question_answer_tts(
        self,
        question: str,
        answer: str
    ) -> dict:
        """
        Generate TTS for Q&A response
        
        Args:
            question: User's question
            answer: AI's answer
        
        Returns:
            dict with audio_url
        """
        text = f"您的问题是：{question}。回答：{answer}"
        
        # Limit length
        max_chars = 2000
        if len(text) > max_chars:
            text = text[:max_chars] + "。"
        
        return await self.generate_tts(text)
    
    def set_voice(self, voice: str):
        """Set TTS voice"""
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice in valid_voices:
            self.voice = voice
    
    def set_model(self, model: str):
        """Set TTS model"""
        valid_models = ["tts-1", "tts-1-hd"]
        if model in valid_models:
            self.model = model


# Singleton instance
tts_service = TTSService()
