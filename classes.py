from transformers import pipeline
from tabulate import tabulate
from datetime import datetime
from config import *


class Entity:
    def __init__(self):
        self.uid = None
        self.creation_time = datetime.now()

    def pretty_creation_time(self):
        return self.creation_time.strftime("%H:%M, %d.%m.%Y")
    
    def get_duration(self):
        current_time = datetime.now()
        duration = current_time - self.creation_time
        days, seconds = duration.days, duration.seconds
        hours, minutes = divmod(seconds, 3600)
        pretty_duration = '{:02}:{:02}:{02}'.format(int(hours), int(minutes), int(seconds % 60))

        return pretty_duration
    

class User(Entity):
    def __init__(self, username, uid):
        super().__init__()
        self.uid = uid
        self.name = None
        self.username = username
        self.email = None


class Article(Entity):
    def __init__(self, text, category):
        super().__init__()
        self.author = None
        self.text = text
        self.category = category


class ClassifierSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ClassifierSingleton, cls).__new__(cls)
            cls._instance.classifier = pipeline(TASK, model=MODEL)
            cls._instance.candidate_labels = CANDIDATE_LABELS
        return cls._instance

    def get_classifier(self):
        return self._instance.classifier

    def get_candidate_labels(self):
        labels = ''
        for label in self._instance.candidate_labels:
            labels += f'- {label}\n'
        labels += f"\n(Total: {len(self._instance.candidate_labels)} classes)"
        return labels

    def add_candidate_label(self, label):
        self._instance.candidate_labels.append(label)

    def remove_candidate_label(self, label):
        if label in self._instance.candidate_labels:
            self._instance.candidate_labels.remove(label)

    def classify_text(self, text):
        classified = self._instance.classifier(text, self._instance.candidate_labels, multi_label=False)
        mapped_by_class = [(classified['labels'][i], classified['scores'][i]) for i, label in enumerate(classified['labels'])]
        return mapped_by_class

    def pretty_table(self, mapped_by_class):
        data = [mapped_by_class[i] for i, pair in enumerate(mapped_by_class)]
        headers = ["Class", "Probability"]
        formatted_data = [(row[0], "{:.2f}".format(row[1])) for row in data[:5]]
        table = tabulate(formatted_data, headers=headers, tablefmt="outline", colalign=("right", "right"))
        return table
