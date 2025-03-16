import asyncio
from typing import Type, List

from openai import AsyncOpenAI

from src.core import settings
from src.core.config import redis_client_for_performance_monitoring
from src.services.ai_service.ai_text_validator import OpenAITextAnalyzer
from src.services.check_pdf_fields import main_check_pdf_fields
from src.services.pdf_tools.parser_pdf import (
    ParserPDFBase,
    ParserPDFWidget,
)
from src.utils.performance_monitoring.cpu import cpu_monitor_decorator
from src.utils.performance_monitoring.ram import ram_monitor_decorator
from src.utils.validators.text_validator import (
    TextWidgetValidatorUseAI,
)


@cpu_monitor_decorator(r_client=redis_client_for_performance_monitoring)
@ram_monitor_decorator(r_client=redis_client_for_performance_monitoring)
async def main(
    path_to_pdf: List[str],
    parser_type: Type[ParserPDFBase],
    validator_type: Type[TextWidgetValidatorUseAI],
    assistant_instance: OpenAITextAnalyzer,
) -> None:
    await main_check_pdf_fields(
        paths_to_pdf=path_to_pdf,
        widget_parser_type=parser_type,
        validator_type=validator_type,
        ai_assistant=assistant_instance,
    )


if __name__ == "__main__":
    ai_assistant = OpenAITextAnalyzer(
        openai_client=AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY, max_retries=5
        ),
        openai_model=settings.BASE_AI_MODEL,
    )

    asyncio.run(
        main(
            path_to_pdf=["test_pdf.pdf", "document mi.pdf"],
            parser_type=ParserPDFWidget,
            validator_type=TextWidgetValidatorUseAI,
            assistant_instance=ai_assistant,
        )
    )
