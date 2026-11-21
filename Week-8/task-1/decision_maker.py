"""Decision Maker: answers fixed questions about a text, such as "which category?" or "yes or no?".

Usage: python decision_maker.py ["a customer message"]   (default: three example messages)
Model: EmbeddingGemma 2 (440M). Instead of writing a free answer like a chatbot, it scores the
given options in a single step, so the answer is always one of them, with probabilities.
"""

import sys

from mediapipe.tasks.python import BaseOptions, decision

from common import model

messages = sys.argv[1:] or [
    "The app crashes every time I try to log in.",
    "I was charged twice for my subscription this month!",
    "How do I change the language of the app?",
]

# A choice question: which of these categories fits the message best?
category = decision.ChoiceQuestion(criteria={
    "billing": "Refunds, invoices, payments or subscription charges.",
    "technical": "Crashes, login errors or features that do not work.",
    "how-to": "Questions about how to use a feature.",
})
# A yes/no question about the same message. This small model gives low "yes" probabilities
# (about 30% for complaints, 10% for plain questions), so the threshold is lowered from 0.5 to 0.25.
complaint = decision.BooleanQuestion(condition="The customer is complaining about a problem.", threshold=0.25)

options = decision.DecisionMakerOptions(
    base_options=BaseOptions(model_asset_path=model("embeddinggemma-2-text-vision-440m.litertlm")),
    max_num_tokens=512,
)
with decision.DecisionMaker.create_from_options(options) as maker:
    for message in messages:
        choice = maker.evaluate_choice(message, category)
        answer = maker.evaluate_boolean(message, complaint)
        scores = ", ".join(f"{k} {p:.0%}" for k, p in choice.probabilities.items())
        print(f"{message!r}")
        print(f"  category: {choice.selected_key} ({scores})")
        print(f"  complaint: {'yes' if answer.value else 'no'} ({answer.probability_true:.0%})")
