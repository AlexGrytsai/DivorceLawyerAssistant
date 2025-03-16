import asyncio
import logging
from typing import List, Dict, Type

from src.services.ai_service.ai_text_validator import AIBaseValidator
from src.services.pdf_tools.annotator import add_comments_to_widgets
from src.services.pdf_tools.parser_pdf import ParserPDFBase
from src.services.pdf_tools.scraper_pdf import (
    ScraperWidgetFromPDF,
    ScrapedPage,
)
from src.utils.validators.text_validator import (
    TextBaseValidator,
    TextWidgetValidatorUseAI,
)

logger = logging.getLogger(__name__)


async def scrap_pdf_fields(path_to_pdf: str) -> List[ScrapedPage]:
    return ScraperWidgetFromPDF(path_to_pdf).scrap_data()


async def prepare_scraped_data(
    parser: ParserPDFBase,
    scraped_data: List[ScrapedPage],
) -> None:
    parser.prepare_data(scraped_data)


async def validate_pdf_fields(
    fields: Dict[str, Dict[str, str]],
    validator: TextBaseValidator,
) -> Dict[str, str]:
    result = await validator.validate_widgets(fields)

    return result


async def check_fields_in_pdf_file(
    path_to_pdf: str,
    parser_instance: ParserPDFBase,
    validator_instance: TextBaseValidator,
) -> None:
    logger.info(f"Check PDF fields for '{path_to_pdf}'...")

    fields = await scrap_pdf_fields(path_to_pdf)
    logger.debug(f"Scraped fields: {fields}")

    await prepare_scraped_data(parser_instance, fields)

    errors_in_fields = await validate_pdf_fields(
        parser_instance.widget_data_dict, validator_instance
    )

    logger.info(f"Mistakes in fields on '{path_to_pdf}': {errors_in_fields}")

    logger.info(f"Add comments to PDF '{path_to_pdf}'...")
    await add_comments_to_widgets(
        pdf_path=path_to_pdf, comments=errors_in_fields
    )

    logger.info(f"PDF '{path_to_pdf}' checked successfully")


async def main_check_pdf_fields(
    paths_to_pdf: List[str],
    widget_parser_type: Type[ParserPDFBase],
    validator_type: Type[TextWidgetValidatorUseAI],
    ai_assistant: AIBaseValidator,
) -> None:
    tasks = [
        check_fields_in_pdf_file(
            path_to_pdf=pdf,
            parser_instance=widget_parser_type(),
            validator_instance=validator_type(ai_assistant=ai_assistant),
        )
        for pdf in paths_to_pdf
    ]

    await asyncio.gather(*tasks)
