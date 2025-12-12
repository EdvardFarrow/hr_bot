import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.parser import content_parser


pytestmark = pytest.mark.asyncio


@patch("app.services.parser.httpx.AsyncClient")
async def test_extract_text_from_url(mock_client_cls):
    """
    Link Extractor Test (with httpx mock)
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = (
        "<html><body><h1>Hello World</h1><p>Python Developer</p></body></html>"
    )

    mock_client = mock_client_cls.return_value.__aenter__.return_value
    mock_client.get.return_value = mock_response

    text = await content_parser.extract_text_from_url("http://example.com")

    assert "Hello World" in text
    assert "Python Developer" in text
    assert "<html>" not in text


@patch("app.services.parser.PdfReader")
async def test_extract_text_from_pdf(mock_pdf_reader):
    mock_page = Mock()
    mock_page.extract_text.return_value = "Python Developer Resume"

    mock_pdf_instance = mock_pdf_reader.return_value
    mock_pdf_instance.pages = [mock_page]

    fake_file_content = b"%PDF-1.4..."
    text = await content_parser.extract_text_from_pdf(fake_file_content)

    assert "Python Developer Resume" in text


@patch("app.services.parser.PdfReader")
async def test_extract_text_from_pdf_error(mock_pdf_reader):
    mock_pdf_reader.side_effect = Exception("Corrupted PDF")

    text = await content_parser.extract_text_from_pdf(b"trash data")

    assert not text


@patch("app.services.parser.httpx.AsyncClient")
async def test_extract_text_from_url_error(mock_client_cls):
    mock_client = mock_client_cls.return_value.__aenter__.return_value
    mock_client.get.side_effect = Exception("Connection Timeout")

    text = await content_parser.extract_text_from_url("http://timeout.com")

    assert not text


@patch("app.services.parser.httpx.AsyncClient")
async def test_extract_text_from_url_404(mock_client_cls):
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = mock_client_cls.return_value.__aenter__.return_value
    mock_client.get.return_value = mock_response

    text = await content_parser.extract_text_from_url("http://example.com/404")

    assert not text
