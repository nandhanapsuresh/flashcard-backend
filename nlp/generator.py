import spacy
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Load once when server starts
nlp = spacy.load("en_core_web_sm")

model_name = "mrm8488/t5-base-finetuned-question-generation-ap"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)


def load_models():
    global nlp, tokenizer, model

    if nlp is None:
        nlp = spacy.load("en_core_web_sm")

    if tokenizer is None:
        tokenizer = T5Tokenizer.from_pretrained(model_name)

    if model is None:
        model = T5ForConditionalGeneration.from_pretrained(model_name)


def generate_question(answer: str, context: str) -> str:
    input_text = f"answer: {answer} context: {context}"
    input_ids = tokenizer.encode(
        input_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(input_ids, max_length=64,
                             num_beams=4, early_stopping=True)
    question = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return question.replace("question:", "").strip()


def generate_flashcards(text: str) -> list:
    doc = nlp(text)

    # Step 1: Extract meaningful sentences
    sentences = [
        sent.text.strip()
        for sent in doc.sents
        if len(sent.text.strip()) > 40
    ]

    flashcards = []

    # Step 2: Generate a question for each sentence using T5
    for sentence in sentences[:8]:
        try:
            question = generate_question(sentence, text)
            flashcards.append({
                "question": question,
                "answer": sentence,
                "status": "not_known",
                "review_count": 0
            })
        except Exception as e:
            print(f"Skipping sentence: {e}")
            continue

    return flashcards
