'''
Translate the names in VGGFace2 dataset into English.
You will need to manually install the following libararies:
unidecode
googletrans
wikiapi

This code is modified by Cheng Yi (PRDCSG) on top of code from Feng Wang (UESTC).
'''
import os
import csv
import string
import unidecode
from googletrans import Translator
translator = Translator()
from wikiapi import WikiApi
wiki = WikiApi()

def is_number(uchar):
    return uchar >= u'0' and uchar<=u'9'

def is_alphabet(uchar):
    return (uchar >= u'a' and uchar<=u'z') or (uchar >= u'A' and uchar<=u'Z')

def check_english(name):
    flag = True
    for uchar in name:
        if (not is_alphabet(uchar)) and (not is_number(uchar)) and (uchar != u'\u0020') and (uchar != u'-') and (uchar != u'.'):
            flag = False
    return flag

def non_english_character_count(name):
    count = 0
    for uchar in name:
        if (not is_alphabet(uchar)) and (not is_number(uchar)) and (uchar != u'\u0020') and (uchar != u'-') and (uchar != u'.'):
            count = count + 1
    return count

def get_full_name_from_wiki(name):
    results = wiki.find(name)
    k = 0
    if len(results) > k:
        article = wiki.get_article(results[k])
        new_name = article.summary
        new_name = new_name[:new_name.find('(')-1]
        # if 'refer' exits in the result, then come to next result
        if new_name.find(' refer ') != -1:
            if len(results) > k+1:
                k += 1
                article = wiki.get_article(results[k])
                new_name = article.summary
                new_name = new_name[:new_name.find('(') - 1]
            else:
                return None
        # if name length larger than 50, regard abnormal,extract until ','
        if len(new_name)>=50:
            new_name = new_name[:new_name.find(',') - 1]
            # if still longer than 50, come to next one
            if (len(new_name) >= 50):
                k += 1
                if len(results)>k:
                    article = wiki.get_article(results[k])
                    new_name = article.summary
                    new_name = new_name[:new_name.find('(') - 1]
                    if len(new_name) >= 50:
                        new_name = new_name[:new_name.find(',') - 1]
                else:
                    return None
        table = str.maketrans({key: None for key in string.punctuation + '\r\n'})
        new_name = new_name.translate(table)

        if len(new_name) > 4 and len(new_name) < 50:
            return new_name
        else:
            return None
    else:
        return None

def count_upper(word):
    return len(list(filter(lambda c: c.isupper(), word)))

def is_short_name(name):
    name = name.replace('.','')
    name_split = name.split('_')
    for word in name_split:
        if len(word)==1 or count_upper(word) == len(word):
            return True
    return False

if __name__ == '__main__':
    file = open('vggface2_identity_trans.csv', 'w', encoding="utf8")
    with open('vggface2_identity_correct.csv', 'r', encoding="utf8") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quoting=csv.QUOTE_ALL)
        for row in spamreader:
            name = row[1].strip()[1:-1].replace('.','._').replace('__','_')
            # skip the first line
            if name == 'am':
                continue
            # if not in standard english, need to translate
            if not check_english(name):
                # If half of the names are regular English characters, see it as an accent.
                if non_english_character_count(name) < len(name) / 2:
                    name = unidecode.unidecode(name)
                # Or, take it as a foreign language.
                else:
                    name = translator.translate(name.replace('_', ' ')).text.replace(' ', '_')
                row[1] = ' "' + name + '"'
            print(row)
            ### After translation into standard English,
            # If the name has only one word, we think this is a nickname,
            # then we will try to find the full name via Wikipedia
            if len(name.split('_')) == 1:
                new_row = row
                new_name = get_full_name_from_wiki(name)
                if new_name is not None:
                    new_name = new_name.replace(', ', '_')
                    new_row[1] = ' "' + new_name + '"'
                    file.write(','.join(new_row) + '\n')
                else:
                    row.append('abnormal')
                    file.write(','.join(row) + '\n')
            # If there is only one capital character in one word, we think this is a short name.
            # We will find the best matched full name from wikipedia.
            elif is_short_name(name):
                new_row = row
                new_name = get_full_name_from_wiki(name)
                if new_name is not None:
                    new_name = new_name.replace(', ', '_')
                    new_row[1] = ' "' + new_name + '"'
                    file.write(','.join(new_row) + '\n')
                else:
                    row.append('abnormal')
                    file.write(','.join(row) + '\n')
            else:
                file.write(','.join(row) + '\n')
    file.close()
