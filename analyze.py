import argparse
from collections import defaultdict
import os
import re
import sys
import subprocess
import xmltodict
from utils import FileUtils
import utils
from word_filter import WordFilterFactory


NOUN = 'NN'
VERB = 'VB'
ADJECTIVE = 'JJ'
ADVERB = 'RB'

PARTS_OF_SPEECH = {
    NOUN: ['NN', 'NNS', 'NNP', 'NNPS'],
    VERB: ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
    ADJECTIVE: ['JJ', 'JJR', 'JJS'],
    ADVERB: ['RB', 'RBR', 'RBS']
}


def convert_part_of_speech(part_of_speech):
    d = {
        NOUN: 'n',
        VERB: 'v',
        ADJECTIVE: 'adj',
        ADVERB: 'adv'
    }
    return d[part_of_speech]


def tag_to_part_of_speech():
    d = {}
    for (part_of_speech, tags) in PARTS_OF_SPEECH.iteritems():
        for tag in tags:
            d[tag] = part_of_speech
    return d


TAG_TO_PART_OF_SPEECH = tag_to_part_of_speech()


def analyze(filename, known_words_filepath, not_known_words_filepath, print_example):
    known_words = set(FileUtils.read(known_words_filepath).split())
    not_known_words = set(FileUtils.read(not_known_words_filepath).split())
    tmp_filepath = FileUtils.random_path()
    output_filepath = tmp_filepath + '.xml'
    FileUtils.copy(filename, tmp_filepath)

    croncob_word_list = os.path.join('data', 'corncob_lowercase.txt')
    word_filter = WordFilterFactory.create_word_filter(croncob_word_list)

    cmd = ['java',
           '-cp',
           'stanford-corenlp-full/stanford-corenlp-3.3.1.jar:stanford-corenlp-full/stanford-corenlp-3.3.1-models.jar:stanford-corenlp-full/xom.jar:stanford-corenlp-full/joda-time.jar:stanford-corenlp-full/jollyday.jar:stanford-corenlp-full/ejml-0.23.jar',
           '-Xmx2g',
           'edu.stanford.nlp.pipeline.StanfordCoreNLP',
           '-annotators',
           'tokenize,ssplit,pos,lemma',
           '-file',
           tmp_filepath,
           '-outputDirectory',
           '/tmp/'
    ]
    subprocess.call(cmd)
    raw_output = FileUtils.read(output_filepath)
    d = xmltodict.parse(raw_output)
    sentences = d['root']['document']['sentences']['sentence']

    candidate_words = defaultdict(dict)

    def word_filter_fun(word, lemma, tag):
        del word
        del tag
        return word_filter.isok(lemma)

    def adjective_filter_fun(word, lemma, tag):
        del word
        del lemma
        if tag in ['JJR', 'JJS']:
            return False
        else:
            return True

    filters = [
            word_filter_fun,
            adjective_filter_fun
    ]

    for sentence_dict in sentences:
        tokens = sentence_dict['tokens']['token']
        if not isinstance(tokens, list):
            continue

        last_offset = int(tokens[0]['CharacterOffsetBegin'])
        sentence_raw = ''
        for token in tokens:
            word = token['word']
            begin_offset = int(token['CharacterOffsetBegin'])
            sentence_raw += (begin_offset - last_offset) * ' '
            sentence_raw += word
            last_offset = int(token['CharacterOffsetEnd'])

        for token in tokens:
            word = token['word']
            lemma = token['lemma']
            tag = token['POS']

            if tag in TAG_TO_PART_OF_SPEECH:
                ok = True
                for filter_fun in filters:
                    if not filter_fun(word, lemma, tag):
                        ok = False
                        break
                if ok:
                    candidate_words[(lemma, TAG_TO_PART_OF_SPEECH[tag])] = {
                        'example_sentence': sentence_raw,
                        'word': word
                    }

    not_known = []
    for ((lemma, part_of_speech), d) in candidate_words.iteritems():
        if lemma not in known_words and lemma not in not_known_words:
            not_known.append((lemma, part_of_speech, d))

    for (lemma, part_of_speech, d) in not_known:
        word = d['word']
        example_sentence = d['example_sentence']
        out = '(%s.) %s' % (
            convert_part_of_speech(part_of_speech),
            lemma
            )

        if print_example:
            line = utils.fill_suffix(out, 22, ' ') + ' # ' + example_sentence
            match_pos = re.search(word, example_sentence).start()
            print line.encode('utf-8')
            print ((match_pos + 25) * ' ') + (len(word) * '^')
        else:
            print out.encode('utf-8')


def analyze_argparse(args):
    filename = args.filename
    known_words_filepath = args.known_words
    not_known_words_filepath = args.not_known_words
    print_examples = args.print_examples
    return analyze(filename, known_words_filepath, not_known_words_filepath, print_examples)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    analyze_parser = subparsers.add_parser('analyze')
    analyze_parser.add_argument('filename', type=str)
    analyze_parser.add_argument('known_words', type=str)
    analyze_parser.add_argument('not_known_words', type=str)
    analyze_parser.add_argument('--print-examples', dest='print_examples', action='store_true')
    analyze_parser.set_defaults(func=analyze_argparse)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())