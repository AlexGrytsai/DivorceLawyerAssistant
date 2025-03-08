from src.core.config import redis_client_for_performance_monitoring
from src.pdf_extractor.geometry_utils import GeometryUtils
from src.pdf_extractor.page_formatter import PageFormatter
from src.pdf_extractor.parser_pdf import ParserPDF
from src.pdf_extractor.scraper_pdf import ScraperPDF
from src.pdf_extractor.table_processor import TableProcessor
from src.pdf_extractor.text_processor import TextProcessor
from src.pdf_extractor.widger_processor import WidgetSpanProcessor
from src.utils.performance_monitoring.cpu import cpu_monitor_decorator
from src.utils.performance_monitoring.ram import ram_monitor_decorator


@cpu_monitor_decorator(r_client=redis_client_for_performance_monitoring)
@ram_monitor_decorator(r_client=redis_client_for_performance_monitoring)
def main(path_to_pdf: str) -> None:
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
        table_processor=TableProcessor(geometry_utils=geometric_utils),
        page_formatter=page_formatter,
    )
    parser.prepare_data(scrap_pdf.scrap_data(), is_for_ai=True)
    a = parser.document_as_text
    print(a)


if __name__ == "__main__":
    main(path_to_pdf="test_pdf.pdf")
