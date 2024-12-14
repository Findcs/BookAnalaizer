import asyncio
import PyPDF2
from fastapi import UploadFile


async def get_book_intro(book: UploadFile) -> list[str]:
    keywords = ['введение', 'предисловие']
    pages = []
    with book.file as file:
        pdf = PyPDF2.PdfReader(file)
        num_pages = len(pdf.pages)
        for page_num in range(num_pages):
            if len(pages) == 2:
                break
            page = pdf.pages[page_num]
            text = page.extract_text()
            for keyword in keywords:
                if keyword in text.lower():
                    pages.append(text)
    if not pages:
        raise ValueError("В книге нет введения или предисловия.")

    return pages


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())
