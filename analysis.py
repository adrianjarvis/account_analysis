import csv
import collections
import json
import datetime

DICT_FILE_NAME = 'classifications.json'

classifications_to_print = ['Unknown']


class MonthAccount(object):
    def __init__(self):
        self._incoming = collections.defaultdict(float)
        self._outgoing = collections.defaultdict(float)

    def process(self, entry, classification):
        if entry.is_outgoing():
            self._outgoing[classification] += entry.amount
        else:
            self._incoming[classification] += entry.amount

    def print_summary(self, classifications):
        for name in classifications:
            print(name, end='')
            print('{:>8.2f}'.format(self._outgoing.get(name, 0)), end='')
            print('{:>8.2f}'.format(self._incoming.get(name, 0)))

    def balance(self):
        total = 0.
        for amount in self._outgoing.values():
            total += amount
        for amount in self._incoming.values():
            total += amount
        return total

class Classifier(object):
    def __init__(self):
        self._rules = {}

    def add_classification(self, entry, classification):
        self._rules[entry.name] = classification

    def classify(self, entry):
        return self._rules.get(entry.name)

    def save(self, file_name):
        with open(file_name, 'w') as file_object:
            json.dump(self._rules, file_object, indent=4, separators=(',', ': '))

    def load(self, file_name):
        with open(file_name, 'r') as file_object:
            self._rules = json.load(file_object)


class Entry(object):
    def __init__(self, name, amount, date):
        self.name = name
        self.amount = amount
        self.date = date

    def __str__(self):
        return "Entry({}, {}, {})".format(self.name, self.date, self.amount)

    def is_outgoing(self):
        return self.amount < 0

    def year_month(self):
        return self.date.year, self.date.month


def parse_file(file_name, parse_func):
    with open(file_name, 'r') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            yield parse_func(row)

# ['transumm_family.CSV', 'transumm_joint.CSV']

def parse_entry_from_credit(row):
            name = row[3]
            amount = float(row[2])
            if row[1] == 'D':
                amount *= -1
            date = datetime.datetime.strptime(row[4], '%d/%m/%Y')
            return Entry(name, amount, date)

def parse_entry_from_account(row):
            name = row[1]
            amount = float(row[5])
            date = datetime.datetime.strptime(row[6], '%d/%m/%Y')
            return Entry(name, amount, date)


def main():
    files = {'transumm_family.CSV': parse_entry_from_account,
             'transumm_joint.CSV': parse_entry_from_account,
             'transumm_savings.CSV': parse_entry_from_account,
             'transumm_credit_card.CSV': parse_entry_from_credit}
    totals = collections.defaultdict(MonthAccount)
    classifier = Classifier()
    classifier.load(DICT_FILE_NAME)
    classifications = set()
    for file_name, parse_func in files.items():
        for entry in parse_file(file_name, parse_func):
            classification = classifier.classify(entry)
            if classification is None:
                classification = input("Enter classification for {}:".format(entry))
                classifier.add_classification(entry, classification)
            totals[entry.year_month()].process(entry, classification)
            classifications.add(classification)
            if classification in classifications_to_print:
                print(file_name, entry)
    classifier.save(DICT_FILE_NAME)
    ordered_classes = list(classifications)
    ordered_classes.sort()
    for year_month, summary in totals.items():
        print(year_month)
        summary.print_summary(ordered_classes)
        print('====',summary.balance(),'====')


main()