import io
import logging
import asyncio
from typing import Optional
import httpx
from pypdf import PdfReader
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class ContentParser:
    _DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> Optional[str]:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n".join(text_parts).strip()
            return full_text if full_text else None

        except Exception as e:
            logger.error(f"Error parsing PDF: {e}", exc_info=True)
            return None

    @classmethod
    async def extract_text_from_pdf(cls, file_bytes: bytes) -> Optional[str]:
        """
        Async wrapper for PDF parsing.
        Runs a CPU-bound task in a separate thread to avoid blocking the bot.
        """
        logger.info("Start parsing PDF")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, cls.parse_pdf, file_bytes)

    @classmethod
    async def extract_text_from_url(cls, url: str) -> Optional[str]:
        """
        Parsing data from URL. Return a clear text or None
        """
        logger.info(f"Trying to download data from URL: {url}")

        async with httpx.AsyncClient(
            headers=cls._DEFAULT_HEADERS, follow_redirects=True
        ) as client:
            try:
                response = await client.get(url, timeout=10.0)

                if response.status_code == 403:
                    logger.warning(
                        f"Access denied (403) to {url}. Likely anti-bot protection."
                    )
                    return None

                if response.status_code != 200:
                    logger.warning(f"URL status {response.status_code}: {url}")
                    return None

                soup = BeautifulSoup(response.text, "html.parser")

                # Removing junk
                for tag in soup(
                    ["script", "style", "meta", "noscript", "header", "footer"]
                ):
                    tag.extract()

                text = soup.get_text(separator="\n")

                cleaned_lines = [
                    line.strip() for line in text.splitlines() if line.strip()
                ]
                result = "\n".join(cleaned_lines)

                logger.info(
                    f"Successfully downloaded {len(result)} characters from URL"
                )
                return result

            except httpx.TimeoutException:
                logger.warning(f"Time-out Connection: {url}")
                return None
            except Exception as e:
                logger.error(f"Parsing error URL: {e}")
                return None


content_parser = ContentParser()
