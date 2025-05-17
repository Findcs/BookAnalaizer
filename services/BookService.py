import string
import re

import PyPDF2
from pymystem3 import Mystem

from fastapi import Depends, UploadFile

from configs.Database import Book, User
from modules.get_book_intro.main import get_book_intro
from modules.tags_extract.main import get_keywords
from repositories.RequestRepository import RequestRepository
from schemas.RequestSchema import RequestCreate
from itertools import chain
from nltk import FreqDist


class BookService:
    request_repository: RequestRepository
    def __init__(self, request_repository: RequestRepository = Depends()):
        self.analizator = Mystem()
        self.request_repository = request_repository

    # async def create(self, file: UploadFile, user: User) -> RequestCreate:
    #     result_req = RequestCreate()
    #
    #     req = Book()
    #     req.book = file.file.read()
    #     req.bookTitle = file.filename
    #     req.user_id = user.id
    #     created_req = await self.request_repository.create(req)
    #     intro = await get_book_intro(file)
    #     tags = []
    #     for i in intro:
    #         tags += list(await get_keywords(i))
    #     result: Result = Result()
    #     result.bookTitle = created_req.bookTitle
    #     result.BookId = created_req.id
    #     result.tags = tags
    #     created_result = await self.result_repository.create(result)
    #     return created_result

    async def get_all_user_books(self, user_id):
        return await self.request_repository.get_all_user_books(user_id)

    async def analyze(self, file: UploadFile, user: User):

        book = Book()
        book.book = file.file.read()
        book.bookTitle = file.filename
        book.user_id = user.id
        text = await self.get_book_intro_mystem(file)
        tags = await self.freq_analyze(text)
        book.tags = tags
        book.section_id = 1
        created_book = await self.request_repository.create(book)
        return {
            "id" : book.id ,
            "tags" : book.tags}

    async def freq_analyze(self, text: str):
        """
        Частотный анализ текста
        """
        stop_words = await self.get_stop()
        words = await self.get_words(text)
        text_test = ' '.join(words)
        lemm_text = [word for word in self.analizator.lemmatize(text_test.lower())
                     if word not in stop_words and word not in string.punctuation + '-""...']
        freq_words = [word_freq_pair[0] for word_freq_pair in FreqDist(lemm_text).most_common(11)]
        freq_words.pop(0)
        return freq_words


    async def get_words(self, text: str):
        """
        Получить слова из текста
        """
        stop_words = await self.get_stop()
        return [word for word in re.findall(r"\w+", text) if word not in stop_words]

    async def get_book_intro_mystem(self, book: UploadFile):
        """
        Извлечение введения из книги
        """
        keywords = ['введение', 'предисловие']
        pages = []
        with book.file as file:
            try:
                pdf = PyPDF2.PdfReader(file)
            except:
                return None
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
            return None
        pattern = re.compile(r'[А-ЯЁа-яё]+')
        return ' '.join(re.findall(pattern, ' '.join(pages)))

    async def get_stop(self):
        """
        Загрузка стоп-слов
        """
        with open('stopwords.txt', 'r', encoding="utf-8") as stop_file:
            return [word.strip() for word in stop_file.readlines()]