"""Generate Korean or English sentences with a small built-in n-gram model."""

from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

CORPORA = {
    "한국어": (
        "오늘은 날씨가 맑아서 공원에 산책을 나갔습니다.",
        "아침에 따뜻한 커피를 마시며 책을 읽었습니다.",
        "친구와 함께 새로운 식당에서 점심을 먹었습니다.",
        "창문을 열자 시원한 바람이 방 안으로 들어왔습니다.",
        "주말에는 가족과 가까운 바다에 다녀올 계획입니다.",
        "작은 화분에 물을 주고 햇빛이 잘 드는 곳에 두었습니다.",
        "저녁에는 좋아하는 음악을 들으며 천천히 걸었습니다.",
        "새로운 것을 배우는 일은 언제나 즐겁고 보람 있습니다.",
        "도서관에서 빌린 책은 생각보다 재미있었습니다.",
        "비가 그친 뒤 하늘에 아름다운 무지개가 나타났습니다.",
        "기차를 타고 창밖의 풍경을 바라보며 여행을 시작했습니다.",
        "시장에서 신선한 과일과 채소를 골라 집으로 가져왔습니다.",
        "잠들기 전에 내일 할 일을 차분하게 정리했습니다.",
        "오래 기다린 편지가 오늘 아침 우편함에 도착했습니다.",
        "동네 골목에는 저마다 다른 이야기가 숨어 있습니다.",
        "따뜻한 국을 함께 나누며 즐거운 저녁 시간을 보냈습니다.",
        "운동을 마친 뒤 물을 마시고 잠시 휴식을 취했습니다.",
        "햇살이 비치는 책상에서 새로운 아이디어를 적었습니다.",
        "박물관에서 오래된 그림과 유물을 천천히 감상했습니다.",
        "작은 변화가 모이면 좋은 습관을 만들 수 있습니다.",
        "회의가 끝난 뒤 중요한 내용을 노트에 간단히 정리했습니다.",
        "익숙한 길도 천천히 걸으면 새로운 모습을 발견할 수 있습니다.",
        "오후에는 창가에 앉아 따뜻한 차를 마셨습니다.",
        "준비한 재료를 손질하고 저녁 식사를 시작했습니다.",
        "서점에서 마음에 드는 엽서와 공책을 골랐습니다.",
        "버스 정류장에서 만난 이웃과 반갑게 인사를 나눴습니다.",
        "산책길에는 계절을 알리는 작은 꽃들이 피어 있었습니다.",
        "하루 동안 있었던 일을 가족에게 이야기해 주었습니다.",
        
        "필요한 물건을 목록에 적어 두면 장을 보기 편합니다.",
        "잠시 쉬었다가 남은 일을 하나씩 마무리했습니다.",
        "낯선 도시에 도착하자 거리의 활기찬 분위기가 느껴졌습니다.",
        "정성껏 만든 음식을 이웃과 함께 나누었습니다.",
        "아침마다 짧게 몸을 풀면 하루를 가볍게 시작할 수 있습니다.",
        "오래된 사진을 보며 즐거웠던 순간을 떠올렸습니다.",
        "창밖으로 보이는 나무가 바람에 천천히 흔들렸습니다.",
        "필요한 정보를 찾기 위해 자료를 꼼꼼하게 살펴보았습니다.",
        "비가 오는 날에는 집에서 조용히 음악을 듣곤 합니다.",
        "친구가 추천해 준 카페는 생각보다 아늑하고 편안했습니다.",
        "계획을 조금 바꾸었지만 덕분에 여유로운 시간을 보냈습니다.",
    ),
    "English": (
        "The morning sun filled the quiet room with warm light.",
        "I walked through the park and listened to the birds.",
        "She found an interesting book at the local library.",
        "We cooked dinner together and shared stories from the day.",
        "A cool breeze came through the open window.",
        "They plan to visit the coast during the weekend.",
        "He wrote a short note before leaving for work.",
        "Learning a new skill can make an ordinary day feel special.",
        "The small garden looked brighter after the rain.",
        "My friends brought fresh fruit to the picnic.",
        "The train moved slowly past fields and wooden houses.",
        "After lunch, we took a walk along the river.",
        "A good idea sometimes appears when we take a quiet break.",
        "The old neighborhood has many welcoming little shops.",
        "She watered the plants and placed them near the window.",
        "We watched the clouds change shape in the evening sky.",
        "The museum displayed photographs from a different century.",
        "He made a simple plan and followed it one step at a time.",
        "A warm bowl of soup made the cold evening more comfortable.",
        "The letter arrived just as the rain began to fall.",
        "We wrote down a few ideas before starting the project.",
        "The market was busy, but everyone seemed to be in a good mood.",
        "She opened the curtains and let the afternoon light inside.",
        "A short break helped us return to the task with fresh energy.",
        "He checked the map before choosing a quieter road.",
        "The children built a small fort from blankets and cushions.",
        "I like to make a simple breakfast when I have enough time.",
        "They sat by the window and watched the rain pass over the town.",
        "The new recipe was easy to follow and tasted wonderful.",
        "We found a peaceful place to rest beneath the trees.",
        "She kept a notebook nearby to record useful thoughts.",
        "The journey felt shorter because we had plenty to talk about.",
        "He thanked the staff for their help and patience.",
        "Fresh bread and warm tea made the kitchen smell inviting.",
        "The path became narrow as it climbed toward the hill.",
        "I saved the message so I could read it again later.",
        "A little preparation can make a busy morning much easier.",
        "The room grew quiet as the music came to an end.",
        "They chose a familiar place where everyone could relax.",
    ),
}

WORD_PATTERN = re.compile(r"[가-힣]+|[A-Za-z]+(?:'[A-Za-z]+)?|\d+|[.!?]")
END_MARKS = {".", "!", "?"}
START = "<START>"
QUANTITY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*([kKmM]?)")
PROGRESS_INTERVAL = 100_000
LINE_BREAK_PROBABILITY = 0.2


def parse_token_count(value: str) -> int:
    """Parse a token target with optional K (thousand) or M (million) suffix."""
    match = QUANTITY_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError("숫자 또는 K/M 단위로 입력하세요. 예: 500, 1K, 1M, 3M")

    number, suffix = match.groups()
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000}[suffix.lower()]
    try:
        result = Decimal(number) * multiplier
    except InvalidOperation as exc:
        raise ValueError("올바른 숫자를 입력하세요.") from exc
    if result != result.to_integral_value() or result < 1:
        raise ValueError("토큰 수는 1 이상의 정수여야 합니다.")
    return int(result)


NGramModel = dict[int, dict[tuple[str, ...], Counter[str]]]


def _build_model(language: str) -> NGramModel:
    """Train unigram, bigram, and trigram next-word counts."""
    transitions: NGramModel = {
        order: defaultdict(Counter) for order in (1, 2, 3)
    }
    for sentence in CORPORA[language]:
        words = WORD_PATTERN.findall(sentence)
        padded_words = [START, START, START, *words]
        for index in range(3, len(padded_words)):
            next_word = padded_words[index]
            for order in (1, 2, 3):
                context = tuple(padded_words[index - order : index])
                transitions[order][context][next_word] += 1
    return transitions


def _sample_next_word(
    model: NGramModel,
    history: list[str],
) -> str:
    selected_order = random.choices(
        (3, 2, 1),
        weights=(0.93, 0.065, 0.005),
        k=1,
    )[0]
    for order in range(selected_order, 0, -1):
        context = tuple(history[-order:])
        choices = model[order].get(context)
        if choices:
            if len(choices) == 1:
                return next(iter(choices))
            words, counts = zip(*choices.items())
            return random.choices(words, weights=counts, k=1)[0]
    raise RuntimeError("학습한 문맥에서 다음 단어를 찾지 못했습니다.")


def _generate_sentence(
    model: NGramModel,
    language: str,
) -> str:
    words: list[str] = []
    history = [START, START, START]
    for _ in range(30):
        word = _sample_next_word(model, history)
        words.append(word)
        if word in END_MARKS:
            break
        history.append(word)

    if not words:
        raise RuntimeError(f"{language} 문장을 생성할 수 없습니다.")
    if words[-1] not in END_MARKS:
        words.append(".")

    sentence = ""
    for word in words:
        if word in END_MARKS:
            sentence = sentence.rstrip() + word
        else:
            sentence += (" " if sentence else "") + word
    return sentence


def estimate_token_count(text: str) -> int:
    """Count tokens with OpenAI's cl100k_base tokenizer."""
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            "정확한 토큰 수 계산에는 tiktoken이 필요합니다. "
            "`pip install tiktoken`을 실행하세요."
        ) from exc

    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text, disallowed_special=()))


def _load_tokenizer():
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            "정확한 토큰 수 계산에는 tiktoken이 필요합니다. "
            "`pip install tiktoken`을 실행하세요."
        ) from exc
    return tiktoken.get_encoding("cl100k_base")


def _sentence_separator(sentence_count: int) -> str:
    if sentence_count == 0:
        return ""
    return "\n" if random.random() < LINE_BREAK_PROBABILITY else " "


def generate_sentences(token_count: int, language: str) -> str:
    """Generate complete sentences until the tokenizer count reaches the target."""
    if token_count < 1:
        raise ValueError("토큰 수는 1 이상이어야 합니다.")
    if language not in CORPORA:
        raise ValueError("언어는 '한국어' 또는 'English'를 선택해야 합니다.")

    encoding = _load_tokenizer()
    model = _build_model(language)
    sentences: list[str] = []
    estimated_total = 0
    while estimated_total < token_count:
        sentence = _generate_sentence(model, language)
        prefix = _sentence_separator(len(sentences))
        sentences.append(prefix + sentence)
        estimated_total += len(
            encoding.encode(prefix + sentence, disallowed_special=())
        )

    text = "".join(sentences)
    actual_total = len(encoding.encode(text, disallowed_special=()))
    while actual_total < token_count:
        ratio = actual_total / estimated_total
        average_sentence_tokens = estimated_total / len(sentences)
        estimated_needed = int(
            (token_count - actual_total) / ratio + average_sentence_tokens
        ) + 1
        estimated_added = 0
        while estimated_added < estimated_needed:
            sentence = _generate_sentence(model, language)
            prefix = _sentence_separator(len(sentences))
            sentences.append(prefix + sentence)
            sentence_tokens = len(
                encoding.encode(prefix + sentence, disallowed_special=())
            )
            estimated_total += sentence_tokens
            estimated_added += sentence_tokens
        text = "".join(sentences)
        actual_total = len(encoding.encode(text, disallowed_special=()))
    return text


def generate_to_file(
    token_count: int,
    language: str,
    output_path: str | Path,
) -> int:
    """Stream generated sentences to disk and return the tokenizer token count."""
    if token_count < 1:
        raise ValueError("토큰 수는 1 이상이어야 합니다.")
    if language not in CORPORA:
        raise ValueError("언어는 '한국어' 또는 'English'를 선택해야 합니다.")

    encoding = _load_tokenizer()
    model = _build_model(language)
    estimated_total = 0
    sentence_count = 0
    next_progress = PROGRESS_INTERVAL
    output = Path(output_path)

    with output.open("w", encoding="utf-8", newline="") as file:
        while estimated_total < token_count:
            sentence = _generate_sentence(model, language)
            prefix = _sentence_separator(sentence_count)
            file.write(prefix)
            file.write(sentence)
            sentence_tokens = len(
                encoding.encode(prefix + sentence, disallowed_special=())
            )
            estimated_total += sentence_tokens
            sentence_count += 1
            if estimated_total >= next_progress:
                print(f"\r생성 중: 약 {estimated_total:,} 토큰", end="", flush=True)
                next_progress += PROGRESS_INTERVAL

    token_total = len(
        encoding.encode(output.read_text(encoding="utf-8"), disallowed_special=())
    )
    while token_total < token_count:
        ratio = token_total / estimated_total
        average_sentence_tokens = estimated_total / sentence_count
        estimated_needed = int(
            (token_count - token_total) / ratio + average_sentence_tokens
        ) + 1
        estimated_added = 0
        with output.open("a", encoding="utf-8", newline="") as file:
            while estimated_added < estimated_needed:
                sentence = _generate_sentence(model, language)
                prefix = _sentence_separator(sentence_count)
                file.write(prefix)
                file.write(sentence)
                sentence_tokens = len(
                    encoding.encode(prefix + sentence, disallowed_special=())
                )
                estimated_total += sentence_tokens
                estimated_added += sentence_tokens
                sentence_count += 1
        token_total = len(
            encoding.encode(output.read_text(encoding="utf-8"), disallowed_special=())
        )

    if estimated_total >= PROGRESS_INTERVAL:
        print()
    return token_total


def main() -> None:
    try:
        token_count = parse_token_count(input("목표 토큰 수를 입력하세요 (예: 500, 1K, 1M): "))
    except ValueError as exc:
        raise SystemExit(str(exc)) from None

    print("언어를 선택하세요: 1) 한국어  2) English")
    language_choice = input("선택 (1/2): ").strip()
    languages = {"1": "한국어", "2": "English"}
    language = languages.get(language_choice)
    if language is None:
        raise SystemExit("언어는 1 또는 2로 선택하세요.")
    output_path = input(
        "저장 파일 경로를 입력하세요 (기본값: generated_sentences.txt): "
    ).strip()
    if not output_path:
        output_path = "generated_sentences.txt"

    try:
        actual_count = generate_to_file(token_count, language, output_path)
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"완료: {actual_count:,} 토큰 (목표: {token_count:,})")
    print(f"결과 파일: {Path(output_path).resolve()}")
    print("※ 토큰은 cl100k_base 기준이며, 다른 모델의 토크나이저와는 다를 수 있습니다.")


if __name__ == "__main__":
    main()
