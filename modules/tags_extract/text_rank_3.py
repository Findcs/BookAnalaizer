import json
import re
import operator

import nltk

debug = False
test = True


def is_number(s):
    try:
        float(s) if '.' in s else int(s)
        return True
    except ValueError:
        return False


def load_stop_words(stop_word_file):
    stop_words = []
    with open(stop_word_file, 'r', encoding='utf-8') as file:
        stop_words += json.loads(file.read())
    return stop_words


def separate_words(text, min_word_return_size):
    splitter = re.compile('[^a-zA-Z0-9_\\+\\-/]')
    words = []
    for single_word in splitter.split(text):
        current_word = single_word.strip().lower()
        if len(current_word) > min_word_return_size and current_word != '' and not is_number(current_word):
            words.append(current_word)
    return words


def split_sentences(text):
    sentence_delimiters = re.compile(u'[.!?,;:\t\\\\"\\(\\)\\\'\u2019\u2013]|\\s\\-\\s')
    sentences = sentence_delimiters.split(text)
    return sentences


def build_stop_word_regex(stop_word_file_path):
    stop_word_list = load_stop_words(stop_word_file_path)
    stop_word_regex_list = []
    for word in stop_word_list:
        word_regex = r'\b' + re.escape(word) + r'(?![\w-])'
        stop_word_regex_list.append(word_regex)
    print(stop_word_regex_list)
    stop_word_pattern = re.compile('|'.join(stop_word_regex_list), re.IGNORECASE)
    return stop_word_pattern


def generate_candidate_keywords(sentence_list, stopword_pattern):
    phrase_list = []
    for s in sentence_list:
        tmp = re.sub(stopword_pattern, '|', s.strip())
        phrases = tmp.split("|")
        for phrase in phrases:
            phrase = phrase.strip().lower()
            if phrase != "":
                phrase_list.append(phrase)
    return phrase_list


def calculate_word_scores(phraseList):
    word_frequency = {}
    word_degree = {}
    for phrase in phraseList:
        word_list = separate_words(phrase, 0)
        word_list_length = len(word_list)
        word_list_degree = word_list_length - 1
        for word in word_list:
            word_frequency.setdefault(word, 0)
            word_frequency[word] += 1
            word_degree.setdefault(word, 0)
            word_degree[word] += word_list_degree  # orig.
    for item in word_frequency:
        word_degree[item] = word_degree[item] + word_frequency[item]

    word_score = {}
    for item in word_frequency:
        word_score.setdefault(item, 0)
        word_score[item] = word_degree[item] / (word_frequency[item] * 1.0)  # orig.
    return word_score


def generate_candidate_keyword_scores(phrase_list, word_score):
    keyword_candidates = {}
    for phrase in phrase_list:
        keyword_candidates.setdefault(phrase, 0)
        word_list = separate_words(phrase, 0)
        candidate_score = 0
        for word in word_list:
            candidate_score += word_score[word]
        keyword_candidates[phrase] = candidate_score
    return keyword_candidates


def preprocess_text(t: str):
    text = re.sub(r"([а-яё]+) ([а-яё])-\n([а-яё]+)", r"\1\2\3", t, flags=re.IGNORECASE)
    text = re.sub(r"([а-яё]+) ([а-яё])-([а-яё]+)", r"\1\2\3", text, flags=re.IGNORECASE)
    text = re.sub("[^а-яА-ЯЁёa-zA-Z]", " ", text)
    text = re.sub(" {2,}", " ", text)
    return text


class Rake(object):
    def __init__(self, stop_words_path):
        self.stop_words_path = stop_words_path
        self.__stop_words_pattern = build_stop_word_regex(stop_words_path)

    def run(self, text):
        text = preprocess_text(text)
        sentence_list = split_sentences(text)

        phrase_list = generate_candidate_keywords(sentence_list, self.__stop_words_pattern)

        word_scores = calculate_word_scores(phrase_list)

        keyword_candidates = generate_candidate_keyword_scores(phrase_list, word_scores)

        sorted_keywords = sorted(keyword_candidates.items(), key=operator.itemgetter(1), reverse=True)
        return sorted_keywords


if test:
    text = """
    Прежде чем решать задачу – прочитай условие.  \nЖак Адамар  \nПРЕДИСЛОВИЕ  \nРаздел «Арифметические основы ЭВМ» дисциплины «Дискретная м а-\nтематика» явля ется одним из первых специальных курсов, которые форм и-\nруют у студентов понимание  основополагающих вопросов организации \nЭВМ, принципы построения отдельных устройств ЭВМ, их взаимосвязь. Он \nдолжен сформировать начальные знания для лучшего понимания последу ю-\nщих спецдисциплин.  \nОсновная цель настоящего учебного пособия – помочь студенту, п ри-\nступившему к изучению арифметики ЭВМ, приобрести теоретические знания \nи практические навыки представления чисел и выполнения основных ари ф-\nметических операций.  \nРассматриваемый в пособии теоретический материал сопровождается \nбольшим количеством примеров, ч то делает более понятным излагаемый м а-\nтериал и упрощает выполнение домашних заданий.  \nСледует отметить, что в последние годы литература, освещающая ари ф-\nметику ЭВМ, не выпускалась. Пособие, в некоторой части, устраняет этот \nинформационный пробел.  \nВ Приложени ях приводятся варианты домашних заданий и именной о б-\nзор известных математиков, внесших вклад в формирование арифметики  как \nматематической науки.  \n  """
    sentenceList = split_sentences(text)
    stoppath = "stopwords.json"
    stopwordpattern = build_stop_word_regex(stoppath)
    phraseList = generate_candidate_keywords(sentenceList, stopwordpattern)
    wordscores = calculate_word_scores(phraseList)
    keywordcandidates = generate_candidate_keyword_scores(phraseList, wordscores)
    # if debug: print(keywordcandidates)
    sortedKeywords = sorted(keywordcandidates.items(), key=operator.itemgetter(1), reverse=True)
    # if debug: print(sortedKeywords)
    totalKeywords = len(sortedKeywords)
    # if debug: print(totalKeywords)
    # print(sortedKeywords[0:(totalKeywords // 3)])
    rake = Rake("stopwords.json")
    keywords = rake.run(text)
    print(keywords)
