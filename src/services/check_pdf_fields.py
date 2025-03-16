import logging
from typing import List, Dict

from src.services.pdf_tools.annotator import add_comments_to_widgets
from src.services.pdf_tools.parser_pdf import ParserPDFBase
from src.services.pdf_tools.scraper_pdf import (
    ScraperWidgetFromPDF,
    ScrapedPage,
)
from src.utils.validators.text_validator import TextBaseValidator

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
    parser: ParserPDFBase,
    validator: TextBaseValidator,
) -> None:
    logger.info(f"Check PDF fields for '{path_to_pdf}'...")

    fields = await scrap_pdf_fields(path_to_pdf)
    logger.debug(f"Scraped fields: {fields}")

    await prepare_scraped_data(parser, fields)

    errors_in_fields = await validate_pdf_fields(
        parser.widget_data_dict, validator
    )

    logger.info(f"Mistakes in fields on '{path_to_pdf}': {errors_in_fields}")

    logger.info(f"Add comments to PDF '{path_to_pdf}'...")
    add_comments_to_widgets(pdf_path=path_to_pdf, comments=errors_in_fields)

    logger.info(f"PDF '{path_to_pdf}' checked successfully")
