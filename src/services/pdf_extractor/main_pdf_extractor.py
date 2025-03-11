from src.services.pdf_extractor.geometry_utils import GeometryUtils
from src.services.pdf_extractor.page_formatter import PageFormatter
from src.services.pdf_extractor.parser_pdf import ParserPDF
from src.services.pdf_extractor.scraper_pdf import ScraperPDF
from src.services.pdf_extractor.table_processor import TableProcessor
from src.services.pdf_extractor.text_processor import TextProcessor
from src.services.pdf_extractor.widger_processor import WidgetSpanProcessor


def main_pdf_extractor(path_to_pdf: str) -> str:
    scrap_pdf = ScraperPDF(path_to_pdf)

    geometric_utils = GeometryUtils()

    text_processor = TextProcessor(geometry_utils=geometric_utils)
    table_processor = TableProcessor(geometry_utils=geometric_utils)
    widget_processor = WidgetSpanProcessor(
        geometry_utils=geometric_utils,
        text_processor=text_processor,
    )

    page_formatter = PageFormatter(
        text_processor=text_processor,
        table_processor=table_processor,
        widget_processor=widget_processor,
    )

    parser = ParserPDF(
        text_processor=text_processor,
        table_processor=table_processor,
        widget_processor=widget_processor,
        page_formatter=page_formatter,
    )

    parser.prepare_data(scrap_pdf.scrap_data(), is_for_ai=True)

    return parser.document_as_text
