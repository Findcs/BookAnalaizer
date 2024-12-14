import asyncio
import re
import string

import numpy as np
import math
from nltk import WordNetLemmatizer, word_tokenize
from nltk.corpus import stopwords
import nltk
import pymorphy3
from pymystem3 import Mystem

morph = pymorphy3.MorphAnalyzer(lang='ru')
stopwords = stopwords.words("russian")
wordnet_lemmatizer = WordNetLemmatizer()

MAX_ITERATIONS = 50
d = 0.85
threshold = 0.0001
wanted_POS = ['NN', 'NNS', 'NNP', 'NNPS', 'JJ', 'JJR', 'JJS', 'VBG', 'FW']
wanted_PYMORPHY = ['NOUN', 'ADJF', 'GRND']
adjective_tags = ['JJ', 'JJR', 'JJS']


def process_text(text: str):
    text = re.sub(r"([а-яё]+) ([а-яё])-\n([а-яё]+)", r"\1\2\3", text, flags=re.IGNORECASE)
    text = re.sub(r"([а-яё]+) ([а-яё])-([а-яё]+)", r"\1\2\3", text, flags=re.IGNORECASE)
    text = re.sub("[^а-яА-ЯЁёa-zA-Z]", " ", text)
    text = word_tokenize(text)
    PYMORPHY_tag = []
    lemmatized_text = []
    for t in text:
        item = morph.parse(t)[0]
        PYMORPHY_tag.append(item)
        lemmatized_text.append(item.word)

    for word in PYMORPHY_tag:
        if word.tag.POS not in wanted_PYMORPHY:
            stopwords.append(word.word)

    processed_text = []
    for word in lemmatized_text:
        if word not in stopwords:
            processed_text.append(word)

    return processed_text, lemmatized_text


async def get_phrases(text) -> list[list[str]]:
    phrases = []
    phrase = " "
    for word in text:
        if word in stopwords:
            if phrase != " ":
                phrases.append(str(phrase).strip().split())
            phrase = " "
        elif word not in stopwords:
            phrase += str(word)
            phrase += " "
    return phrases


async def get_keywords(text: str) -> list[str]:
    processed_text, lemmatized_text = process_text(text)
    phrases = await get_phrases(lemmatized_text)
    vocab = list(set(processed_text))
    vocab_len = len(vocab)
    # граф
    weighted_edge = np.zeros((vocab_len, vocab_len), dtype=np.float32)
    # счет
    score = np.zeros((vocab_len), dtype=np.float32)
    window_size = 3
    covered_coocurrences = []
    for i in range(0, vocab_len):
        score[i] = 1
        for j in range(0, vocab_len):
            if j == i:
                weighted_edge[i][j] = 0
            else:
                for ww_start in range(0, len(processed_text) - window_size + 1):
                    ww_end = ww_start + window_size
                    ww_slice = processed_text[ww_start:ww_end]
                    if ww_slice and (vocab[i] in ww_slice and vocab[j] in ww_slice):
                        index_of_i = ww_start + ww_slice.index(vocab[i])
                        index_of_j = ww_start + ww_slice.index(vocab[j])
                        if [index_of_i, index_of_j] not in covered_coocurrences:
                            weighted_edge[i][j] += 1 / math.fabs(index_of_i - index_of_j)
                            covered_coocurrences.append([index_of_i, index_of_j])

    inout = np.zeros(vocab_len, dtype=np.float32)
    for i in range(0, vocab_len):
        for j in range(0, vocab_len):
            inout[i] += weighted_edge[i][j]
    for iter in range(0, MAX_ITERATIONS):
        prev_score = np.copy(score)
        for i in range(0, vocab_len):
            summation = 0
            for j in range(0, vocab_len):
                if weighted_edge[i][j] != 0:
                    summation += (weighted_edge[i][j] / inout[j]) * score[j]
            score[i] = (1 - d) + d * (summation)
        if np.sum(np.fabs(prev_score - score)) <= threshold:
            print("Converging at iteration " + str(iter) + "....")
            break
    for i in range(0, vocab_len):
        print("Score of " + vocab[i] + ": " + str(score[i]))
    unique_phrases = []
    for phrase in phrases:
        if phrase not in unique_phrases:
            unique_phrases.append(phrase)
    for word in vocab:
        for phrase in unique_phrases:
            if (word in phrase) and ([word] in unique_phrases) and (len(phrase) > 1):
                unique_phrases.remove([word])
    phrase_scores = []
    keywords = []
    for phrase in unique_phrases:
        phrase_score = 0
        keyword = ''
        for word in phrase:
            keyword += str(word)
            keyword += " "
            phrase_score += score[vocab.index(word)]
        phrase_scores.append(phrase_score)
        keywords.append(keyword.strip())

    print(unique_phrases)
    sorted_index = np.flip(np.argsort(phrase_scores), 0)
    keywords_num = 10
    print("Keywords:\n")
    for i in range(0, keywords_num):
        print(str(keywords[sorted_index[i]]) + ", ", )


async def main():
    keywords = await get_keywords("""
    Прежде чем решать задачу – прочитай условие.  \nЖак Адамар  \nПРЕДИСЛОВИЕ  \nРаздел «Арифметические основы ЭВМ» дисциплины «Дискретная м а-\nтематика» явля ется одним из первых специальных курсов, которые форм и-\nруют у студентов понимание  основополагающих вопросов организации \nЭВМ, принципы построения отдельных устройств ЭВМ, их взаимосвязь. Он \nдолжен сформировать начальные знания для лучшего понимания последу ю-\nщих спецдисциплин.  \nОсновная цель настоящего учебного пособия – помочь студенту, п ри-\nступившему к изучению арифметики ЭВМ, приобрести теоретические знания \nи практические навыки представления чисел и выполнения основных ари ф-\nметических операций.  \nРассматриваемый в пособии теоретический материал сопровождается \nбольшим количеством примеров, ч то делает более понятным излагаемый м а-\nтериал и упрощает выполнение домашних заданий.  \nСледует отметить, что в последние годы литература, освещающая ари ф-\nметику ЭВМ, не выпускалась. Пособие, в некоторой части, устраняет этот \nинформационный пробел.  \nВ Приложени ях приводятся варианты домашних заданий и именной о б-\nзор известных математиков, внесших вклад в формирование арифметики  как \nматематической науки.  \n  """)
    print(keywords)


if __name__ == '__main__':
    asyncio.run(main())
