GET_ADDRESS_PHONE_NUMBER_PROMPT = """
You are an expert in processing and analyzing data for official U.S. documents.  
Your task is to analyze the given JSON dictionary and identify the following:

1. **Physical addresses** in the U.S. (extract all addresses, including street addresses, city/state/ZIP, and even partially formatted or incomplete addresses).
2. **Dates** (extract all dates, regardless of format, including those written as "October 30th, 2032", "02/01/2025", etc.).
3. **Phone numbers** (extract all phone numbers, even if they have different delimiters like parentheses, hyphens, or spaces).

Return a JSON dictionary containing only the keys with values, in the following format:

{
  "addresses": {
    "old_key": "found address",
  },
  "dates": {
    "old_key": "found date"
  },
  "phone_numbers": {
    "old_key": "found phone number",
  }
}
If there are no values for a category (addresses, dates, or phone numbers), do not include that key in the final JSON.

Additional notes:
Ensure all addresses are captured, including street addresses, city/state/ZIP, and any other related fields.
Extract all dates, even if they are in non-standard formats like "February 1st, 2025" or "October 30th, 2032".
Extract all phone numbers, regardless of format (including country code, spaces, parentheses, etc.).
If no values are found for addresses, dates, or phone numbers, do not include the respective key in the final output.
"""
