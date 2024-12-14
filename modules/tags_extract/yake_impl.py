import json
import math
import re
import string
from collections import defaultdict
from pathlib import Path

import nltk
import numpy
import pymorphy3
from nltk import ngrams


class Yake:
    def __init__(self):
        self.words = defaultdict(set)
        self.contexts = defaultdict(lambda: ([], []))
        self.morph = pymorphy3.MorphAnalyzer(lang='ru')
        self.features = defaultdict(dict)
        self.surface_to_lexical = {}
        self.candidates = []
        self.sentences = []
        self.text = ''
        with open(Path(__file__).resolve().parent / "stopwords.json", 'r', encoding='utf-8') as file:
            self.stopwords = set(json.loads(file.read()))

    def __preprocess_text(self):
        self.text = re.sub(r"([а-яё]+) ([а-яё])-\n([а-яё]+)", r"\1\2\3", self.text, flags=re.IGNORECASE)
        self.text = re.sub(r"([а-яё]+) ([а-яё])-([а-яё]+)", r"\1\2\3", self.text, flags=re.IGNORECASE)
        self.text = re.sub("\n|«|»|–|…|\d|гг\.", '', self.text)
        self.text = re.sub("предисловие", '', self.text, flags=re.IGNORECASE)
        self.text = re.sub(" {2,}", ' ', self.text)
        self.text = self.text.strip()

    def __generate_candidates(self, from_gr=1, n: int = 3):
        tokens = [t for t in nltk.word_tokenize(self.text) if t not in string.punctuation]
        cands = []
        for i in range(from_gr, n + 1):
            ngr = [ngram for ngram in set(ngrams(tokens, i))]
            cands.extend(ngr)
        for k in cands:
            normal_form_in_stopwords = self.morph.parse(k[0])[0].normal_form.lower() in self.stopwords or \
                                       self.morph.parse(k[-1])[0].normal_form.lower() in self.stopwords
            initial_form_in_stopwords = k[0].lower() in self.stopwords or k[-1].lower() in self.stopwords
            if not normal_form_in_stopwords and not initial_form_in_stopwords:
                self.candidates.append(k)

    def __split_to_sentences(self):
        self.sentences = nltk.sent_tokenize(self.text)

    def __vocabulary_building(self):
        for i, sentence in enumerate(self.sentences):
            shift = sum([len(s) for s in self.sentences[0:i]])
            for j, word in enumerate(nltk.word_tokenize(sentence)):
                index = word.lower()
                self.words[index].add((shift + j, shift, i, word))

    def __feature_extraction(self):
        # get the Term Frequency of each word
        TF = [len(self.words[w]) for w in self.words]

        # get the Term Frequency of non-stop words
        TF_nsw = [len(self.words[w]) for w in self.words if w not in self.stopwords]

        # compute statistics
        mean_TF = numpy.mean(TF_nsw)
        std_TF = numpy.std(TF_nsw)
        max_TF = max(TF)
        for word in self.words:

            # Indicating whether the word is a stopword (vitordouzi change)
            self.features[word]['isstop'] = word in self.stopwords or len(word) < 3

            # Term Frequency
            self.features[word]['TF'] = len(self.words[word])

            # Uppercase/Acronym Term Frequencies
            self.features[word]['TF_A'] = 0
            self.features[word]['TF_U'] = 0
            for (offset, shift, sent_id, surface_form) in self.words[word]:
                if surface_form.isupper() and len(word) > 1:
                    self.features[word]['TF_A'] += 1
                elif surface_form[0].isupper() and offset != shift:
                    self.features[word]['TF_U'] += 1

            # 1. CASING feature
            self.features[word]['CASING'] = max(self.features[word]['TF_A'],
                                                self.features[word]['TF_U'])
            self.features[word]['CASING'] /= 1.0 + math.log(
                self.features[word]['TF'])

            # 2. POSITION feature
            sentence_ids = list(set([t[2] for t in self.words[word]]))
            self.features[word]['POSITION'] = math.log(
                3.0 + numpy.median(sentence_ids))
            self.features[word]['POSITION'] = math.log(
                self.features[word]['POSITION'])

            # 3. FREQUENCY feature
            self.features[word]['FREQUENCY'] = self.features[word]['TF']
            self.features[word]['FREQUENCY'] /= (mean_TF + std_TF)

            # 4. RELATEDNESS feature
            self.features[word]['WL'] = 0.0
            if len(self.contexts[word][0]):
                self.features[word]['WL'] = len(set(self.contexts[word][0]))
                self.features[word]['WL'] /= len(self.contexts[word][0])
            self.features[word]['PL'] = len(set(self.contexts[word][0])) / max_TF

            self.features[word]['WR'] = 0.0
            if len(self.contexts[word][1]):
                self.features[word]['WR'] = len(set(self.contexts[word][1]))
                self.features[word]['WR'] /= len(self.contexts[word][1])
            self.features[word]['PR'] = len(set(self.contexts[word][1])) / max_TF

            self.features[word]['RELATEDNESS'] = 1
            self.features[word]['RELATEDNESS'] += (self.features[word]['WR'] +
                                                   self.features[word]['WL']) * \
                                                  (self.features[word]['TF'] / max_TF)

            # 5. DIFFERENT feature
            self.features[word]['DIFFERENT'] = len(set(sentence_ids))
            self.features[word]['DIFFERENT'] /= len(self.sentences)

            # assemble the features to weight words
            A = self.features[word]['CASING']
            B = self.features[word]['POSITION']
            C = self.features[word]['FREQUENCY']
            D = self.features[word]['RELATEDNESS']
            E = self.features[word]['DIFFERENT']
            self.features[word]['weight'] = (D * B) / (A + (C / D) + (E / D))

    def __contexts_building(self, window=2):
        """Build the contexts of the words for computing the relatedness
        feature. Words that occur within a window of n words are considered as
        context words. Only words co-occurring in a block (sequence of words
        that appear in the vocabulary) are considered.

        Args:
            use_stems (bool): whether to use stems instead of lowercase words
                for weighting, defaults to False.
            window (int): the size in words of the window used for computing
                co-occurrence counts, defaults to 2.
        """
        # loop through sentences
        for i, sentence in enumerate(self.sentences):
            # lowercase the words
            words = [w.lower() for w in nltk.word_tokenize(sentence)]
            # block container
            block = []
            # loop through words in sentence
            for j, word in enumerate(words):
                # skip and flush block if word is not in vocabulary
                if word not in self.words:
                    block = []
                    continue
                # add the left context
                self.contexts[word][0].extend(
                    [w for w in block[max(0, len(block) - window):len(block)]]
                )
                # add the right context
                for w in block[max(0, len(block) - window):len(block)]:
                    self.contexts[w][1].append(word)
                # add word to the current block
                block.append(word)

    def __count_kw(self, kw: str):
        c = 0
        for i in self.candidates:
            if kw == i:
                c += 1
        return c

    def get_n_best(self, n=10):
        res = []
        for c in self.candidates:
            product = 1
            summary = 0
            count = 0
            for ic in c:
                word_features = self.features[ic.lower()]
                product *= word_features.get("weight")
                summary += word_features.get("weight")
                count += 1 if not word_features.get("isstop") else 0

            score = product / (1 + summary + count)
            res.append((' '.join(c), score))

        res.sort(key=lambda x: x[-1], reverse=True)
        return res[:n]

    def generate_keywords(self, text: str, n=5, from_grams=1, to_grams=3, stem=False):
        self.text = text
        self.__preprocess_text()
        self.__split_to_sentences()
        self.__generate_candidates(from_gr=from_grams, n=to_grams)
        self.__vocabulary_building()
        self.__contexts_building()
        self.__feature_extraction()
        candidates = self.get_n_best(n)
        if stem:
            return [self.morph.parse(_[0])[0].normal_form for _ in candidates]
        return [_[0] for _ in candidates]


if __name__ == '__main__':
    text = """
    Прежде чем решать задачу – прочитай условие.  \nЖак Адамар  \nПРЕДИСЛОВИЕ  \nРаздел «Арифметические основы ЭВМ» дисциплины «Дискретная м а-\nтематика» явля ется одним из первых специальных курсов, которые форм и-\nруют у студентов понимание  основополагающих вопросов организации \nЭВМ, принципы построения отдельных устройств ЭВМ, их взаимосвязь. Он \nдолжен сформировать начальные знания для лучшего понимания последу ю-\nщих спецдисциплин.  \nОсновная цель настоящего учебного пособия – помочь студенту, п ри-\nступившему к изучению арифметики ЭВМ, приобрести теоретические знания \nи практические навыки представления чисел и выполнения основных ари ф-\nметических операций.  \nРассматриваемый в пособии теоретический материал сопровождается \nбольшим количеством примеров, ч то делает более понятным излагаемый м а-\nтериал и упрощает выполнение домашних заданий.  \nСледует отметить, что в последние годы литература, освещающая ари ф-\nметику ЭВМ, не выпускалась. Пособие, в некоторой части, устраняет этот \nинформационный пробел.  \nВ Приложени ях приводятся варианты домашних заданий и именной о б-\nзор известных математиков, внесших вклад в формирование арифметики  как \nматематической науки.  \n  """
    yake = Yake()
    print(yake.generate_keywords(text, stem=True, n=5))
