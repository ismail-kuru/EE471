"""Task 1.3: complete a sentence two different ways, each at most 35 words long.

First the plain way, max_length=35, to show why it does not give 35 words; then the fixed way.
"""

from common import show, title
from transformers import pipeline, set_seed

PROMPT = "If I continue to complete all in-class exercises in this modern software practices course,"
MAX_WORDS = 35

generator = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M")
prompt_tokens = len(generator.tokenizer(PROMPT)["input_ids"])


def shorten(text, max_words):
    """Cut the text to max_words words, then back to the last full sentence if there is one."""
    words = " ".join(text.split()[:max_words])
    end = max(words.rfind("."), words.rfind("!"), words.rfind("?"))
    return words[: end + 1] if end > len(PROMPT) else words


def print_options(texts):
    for number, text in enumerate(texts, start=1):
        print()
        show(f"Option {number}", " ".join(text.split()))  # on one line, without the model's line breaks
        show("Words", len(text.split()))


title("Text generation (SmolLM2-360M)")
show("Prompt", f"{PROMPT}  ({len(PROMPT.split())} words, {prompt_tokens} tokens)")

# 1) The plain way. max_length counts tokens, not words, and it includes the prompt,
#    so only 35 - prompt_tokens new tokens are left and the sentence is cut short.
#    The pipeline also sets max_new_tokens=256 by default, which wins over max_length;
#    max_new_tokens=None turns that off, otherwise max_length=35 is silently ignored.
set_seed(42)  # sampling is random; a fixed seed gives the same sentences on every run
plain = generator(PROMPT, max_length=35, max_new_tokens=None, num_return_sequences=2, do_sample=True)
print(f"\n--- 1) max_length=35: 35 tokens in total, only {35 - prompt_tokens} new ones")
print_options([result["generated_text"] for result in plain])

# 2) The fixed way. max_new_tokens counts only the new tokens, so the model has room to finish
#    the sentence; then shorten() counts real words and keeps at most 35.
set_seed(42)
fixed = generator(PROMPT, max_new_tokens=50, num_return_sequences=2, do_sample=True)
print(f"\n--- 2) max_new_tokens=50, then cut to {MAX_WORDS} words at the last full sentence")
print_options([shorten(result["generated_text"], MAX_WORDS) for result in fixed])
