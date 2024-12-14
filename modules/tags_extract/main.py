import asyncio
import json
import re
from pathlib import Path

import nltk
import pymorphy3
from modules.tags_extract.yake_impl import Yake
import string
from nltk import ngrams
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from natasha import NamesExtractor, MorphVocab

morph_vocab = MorphVocab()
names_extractor = NamesExtractor(morph_vocab)
nlp = spacy.load("ru_core_news_sm")
morph = pymorphy3.MorphAnalyzer(lang='ru')
vectorizer = TfidfVectorizer()
yake = Yake()

with open(Path(__file__).resolve().parent / "stopwords.json", 'r', encoding='utf-8') as file:
    stopwords = set(json.loads(file.read())) | set(string.punctuation)

with open(Path(__file__).resolve().parent / "noun_stopwords.json", 'r', encoding='utf-8') as file:
    noun_stopwords = set(json.loads(file.read()))

with open(Path(__file__).resolve().parent / "adj_stopwords.json", 'r', encoding='utf-8') as file:
    adj_stopwords = set(json.loads(file.read()))

with open(Path(__file__).resolve().parent / "verb_stopwords.json", 'r', encoding='utf-8') as file:
    verb_stopwords = set(json.loads(file.read()))


async def process_text(text: str):
    text = re.sub(r"([а-яё]+) ([а-яё])-\n([а-яё]+)", r"\1\2\3", text, flags=re.IGNORECASE)
    text = re.sub(r"([а-яё]+) ([а-яё])-([а-яё]+)", r"\1\2\3", text, flags=re.IGNORECASE)
    text = re.sub(r"([а-яё]+)\s?-\n([а-яё]+)", r"\1\2", text, flags=re.IGNORECASE)
    text = re.sub(r"\s?([а-яё]+[аеёиоуыэюя])\s?-\s?([бвгджзйклмнпрстфхцчшщ][а-яё]+)\s?", r" \1\2 ", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"\s([а-яё]{2}) ([а-яё])-\s([а-яё]+) ([аеёиоуыэюя]{2})\s", r" \1\2\3\4 ", text, flags=re.IGNORECASE)
    text = re.sub(r"([а-яё]+) ые ", r"\1ые ", text, flags=re.IGNORECASE)
    text = re.sub(r"([а-яё]+) ая ", r"\1ая ", text, flags=re.IGNORECASE)
    text = re.sub(r"([а-яё]+) ях ", r"\1ях ", text, flags=re.IGNORECASE)
    text = re.sub(r" ([мргнтчфждлхз]) ([а-яё]+)", r"\1\2 ", text, flags=re.IGNORECASE)
    text = re.sub(r" п ри-", r"при", text, flags=re.IGNORECASE)
    text = re.sub("\n|«|»|–|…|\d{1}|гг\.", '', text)
    text = re.sub("предисловие", '', text, flags=re.IGNORECASE)
    text = re.sub("количе ство", 'количество', text, flags=re.IGNORECASE)
    text = re.sub(" {2,}|\.{2,}", ' ', text)
    return text.strip()


async def get_words_from_brackets(text: str) -> list[str]:
    words = re.findall(r"«([а-яa-zё ]+)»", text, flags=re.IGNORECASE)
    return words


async def get_nlp_keywords(text: str) -> set[str]:
    sents = nltk.sent_tokenize(text)
    phrases = set()
    for s in sents:
        doc = nlp(s)
        for i, token in enumerate(
                doc[:-2]):
            if token.pos_ == "ADJ" and doc[i + 1].pos_ == "NOUN" and token.text.lower() not in adj_stopwords \
                    and doc[i + 1].text.lower() not in noun_stopwords:
                # Прилагательное + существительное
                print('=' * 10)
                print('Прилагательное + существительное')
                print(f"{token.text} {doc[i + 1].text}")
                print('=' * 10)
                phrases.add(f"{token.text} {doc[i + 1].text}")
            elif token.pos_ == "VERB" and doc[i + 1].pos_ == "ADJ" and doc[i + 2].pos_ == "NOUN" \
                    and token.text.lower() not in verb_stopwords and doc[i + 1].text.lower() not in adj_stopwords \
                    and doc[i + 2].text.lower() not in noun_stopwords:
                # Глагол + прилагательное + существительное
                print('=' * 10)
                print('Глагол + прилагательное + существительное')
                print(f"{token.text} {doc[i + 1].text} {doc[i + 2].text}")
                print('=' * 10)
                phrases.add(f"{token.text} {doc[i + 1].text} {doc[i + 2].text}")
            elif token.pos_ == "NOUN" and doc[i + 1].pos_ == "PROPN" \
                    and token.text.lower() not in noun_stopwords and doc[i + 1].text.lower() not in noun_stopwords:
                # Существительное + имя собственное
                print('=' * 10)
                print('Существительное + имя собственное')
                print(f"{token.text} {doc[i + 1].text}")
                print('=' * 10)
                phrases.add(f"{token.text} {doc[i + 1].text}")
            elif token.pos_ == "VERB" and doc[i + 1].pos_ == "NOUN" and doc[i + 1].dep_ == "nmod" and \
                    morph.parse(doc[i + 1].text)[0].tag.case == "gent" \
                    and token.text.lower() not in verb_stopwords and doc[i + 1].text.lower() not in noun_stopwords:
                # Глагол + сущ в родительном падеже
                print('=' * 10)
                print('Глагол + сущ в родительном падеже')
                print(f"{token.text} {doc[i + 1].text}")
                print('=' * 10)
                phrases.add(f"{token.text} {doc[i + 1].text}")
    return phrases


async def get_keywords(text: str) -> list[str]:
    res = set()
    text = await process_text(text)
    names = await get_names(text)
    words_from_brackets = await get_words_from_brackets(text)
    res = res | set(names)
    res = res | set(words_from_brackets)
    nlp_keywords = await get_nlp_keywords(text)
    yake_keywords = yake.generate_keywords(text, from_grams=3, n=5)
    res = res | set(nlp_keywords)
    res = res | set(yake_keywords)
    print("#" * 10)
    print(yake_keywords)
    print("-" * 10)
    print(nlp_keywords)
    print("#" * 10)
    return [_.lower() for _ in res]


async def get_names(text: str) -> list[str]:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PER"]
    return names


async def main():
    text = """3  ВВЕДЕНИЕ  \n \nДанное  учебное пособие предназначено  для иностранных студентов  \nподготовительного отделения и первого курса бакалавриата  всех \nнаправлений  подготовки.  \nПособие  состоит  из пяти  уроков,  каждый  из которых  определяет  \nведущая  разговорная  тема.  В конце  пособия  находятся  Приложение , в \nкоторое  входят  ответы к  заданиям,  и Фразеологический  словарь . \nХарактер  включенного  в пособие  материала  определяется  теми  \nтрудностями,  которые  имеются  у иностранцев,  изучающих  русский  язык.  \nКаждый  урок  на основе  заданий  «Давайте  поговорим»,  «Кинозал»,  \n«Повторите  грамматический материал», «Проверьте свое понимание  \nтекста»  решает определенные речевые  задачи, способствует развитию у  \nучащихся  умения  строить  как монологичес кие, так и диалогические  \nвысказывания.  \nБо́льшую  часть  заданий  можно  выполнять  устно.  \nВ пособии  используются  отрывки  из художественных  произведений,  \nа также материалы  из газет  и журналов.  ',
  '60   \n \nОглавление  \nСтр. \n \n \nВведение  ................................ ................................ ................................ ..... 3 \nТема 1…  ................................ ................................ ................................ ...... 4 \nТема 2…  ................................ ................................ ................................ ..... 15 \nТема 3…  ................................ ................................ ................................ ..... 23 \nТема 4…  ................................ ................................ ................................ ..... 29 \nТема 5…  ................................ ................................ ................................ ..... 37 \nПриложение  ................................ ................................ ..............................  46 \nСписок  использованной литературы  ................................ ......................  59 \nОглавление  ................................ ................................ ................................ . 60 """
    res = await get_keywords(text)
    print(res)


if __name__ == '__main__':
    asyncio.run(main())
