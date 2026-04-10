from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "sqlite:///./agricultural_ai.db"
    allowed_origins: str = "http://localhost:3000"
    app_name: str = "Agricultural AI Advisor"
    openai_model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    system_prompt: str = (
        "أنت مستشار زراعي خبير متخصص في مجال الزراعة. "
        "مهمتك تقديم نصائح وإرشادات زراعية دقيقة وعملية باللغة العربية والإنجليزية. "
        "تخصصك يشمل: زراعة المحاصيل، إدارة التربة، الري، مكافحة الآفات والأمراض النباتية، "
        "الأسمدة، تقنيات الزراعة الحديثة، والممارسات الزراعية المستدامة. "
        "أجب دائماً بشكل واضح ومفيد، وقدم حلولاً عملية وقابلة للتطبيق. "
        "إذا كان السؤال خارج نطاق الزراعة، أخبر المستخدم بلطف أنك متخصص في الاستشارات الزراعية فقط."
    )

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
