from typing import List, Dict, Tuple

from src.services.pdf_extractor.parser_pdf import ParserPDFBase
from src.services.pdf_extractor.scraper_pdf import ScrapedPage, ScraperPDF


def main_scraper(path_to_pdf: str) -> List[ScrapedPage]:
    return ScraperPDF(path_to_pdf).scrap_data()


def prepare_parser_data(
    parser: ParserPDFBase,
    scraped_data: List[ScrapedPage],
) -> None:
    parser.prepare_data(scraped_data, use_widget_label=True)


def extract_pdf_data(
    path_to_pdf: str,
    parser: ParserPDFBase,
) -> Tuple[str, Dict[str, str]]:
    prepare_parser_data(parser, main_scraper(path_to_pdf))

    return parser.document_as_text, parser.widget_data_dict
