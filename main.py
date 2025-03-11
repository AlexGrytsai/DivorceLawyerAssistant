from src.services.pdf_extractor import main_pdf_extractor


# @cpu_monitor_decorator(r_client=redis_client_for_performance_monitoring)
# @ram_monitor_decorator(r_client=redis_client_for_performance_monitoring)
def main(path_to_pdf: str) -> None:
    text = main_pdf_extractor(path_to_pdf)
    print(text)

    # open_ai_client = AsyncOpenAI(
    #     api_key=settings.OPENAI_API_KEY,
    # )
    #
    # ai_analyzer_service = OpenAIAnalyzerService(open_ai_client)
    #
    # # with open("instraction.txt", "r", encoding="utf-8") as file:
    # #     instructions = file.read()
    # print(
    #     asyncio.run(
    #         ai_analyzer_service.analyze_pdf_with_ai(
    #             document_text=text,
    #             us_state="Florida",
    #             # instruction_for_document=instructions,
    #         )
    #     )
    # )


if __name__ == "__main__":
    # main(path_to_pdf="test_pdf.pdf")
    main(path_to_pdf="indigent_status_application.pdf")
