# Это инструмент для обработки латинского текста.

import string

# Определение групп согласных, которые рассматриваются как единое целое при делении на слоги
CONSONANT_GROUPS = [
    "bl", "br", "pl", "pr", "dr", "tr", "cl", "cr", "fr", "fl", "gr", "gl",
    "sp", "st", "sc",
    "ch", "ph", "th", "qu"
]

# Карта соответствия долгих гласных знаков коротким, используется для некоторых проверок
LONG_MARK_MAP = {
    'ā': 'a',
    'ē': 'e',
    'ī': 'i',
    'ō': 'o',
    'ū': 'u',
    'ȳ': 'y'
}

# Определение дифтонгов (двойных гласных)
DIPHTHONGS = ['ae', 'oe', 'au', 'eu', 'ei', 'ui']

# Определение всех гласных (включая долгие)
VOWELS = ['a', 'e', 'i', 'o', 'u', 'y', 'ā', 'ē', 'ī', 'ō', 'ū', 'ȳ']

# Определение всех согласных
CONSONANTS = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p',
              'q', 'r', 's', 't', 'v', 'w', 'x', 'z']

def sounder(word: str) -> list:
    """
    Анализирует каждый символ слова, помечая его как гласную ('v') или согласную ('c').
    Обрабатывает специальные случаи: дифтонги, группы согласных и полугласный характер 'i'.
    Возвращает список, где каждый элемент представляет собой [тип, символ или группа символов].
    """
    if not word:
        return []
    
    chars = []
    word_len = len(word)
    i = 0

    while i < word_len:
        char = word[i]
        if char in LONG_MARK_MAP.keys():
            chars.append(['v', char])
            i += 1
        elif char in ['a', 'e', 'o', 'y']:
            chars.append(['v', char])
            i += 1
        elif char == 'u':
            if i > 0 and word[i-1] == 'q':
                chars.append(['c', char])
            else:
                chars.append(['v', char])
            i += 1
        elif char == 'i':
            if word_len == 1:
                chars.append(['v', char])
                i += 1
                continue
            if i == 0:
                chars.append(['v', char] if word[1] not in VOWELS else ['c', char])
                i += 1
            elif i == word_len - 1:
                chars.append(['v', char])
                i += 1
            else:
                prev_char = word[i-1]
                next_char = word[i+1]
                prev_is_vowel = prev_char in VOWELS
                next_is_vowel = next_char in VOWELS
                chars.append(['c', char] if (prev_is_vowel and next_is_vowel) else ['v', char])
                i += 1
        else:
            matched = False
            if not matched and i + 1 < word_len:
                two_char = word[i:i+2]
                if two_char in CONSONANT_GROUPS:
                    chars.append(['c', two_char])
                    i += 2
                    matched = True
            if not matched:
                chars.append(['c', char])
                i += 1

    pairs_to_merge = []
    for j in range(len(chars) - 1):
        curr_type, curr_char = chars[j]
        next_type, next_char = chars[j+1]
        if curr_type == 'v' and next_type == 'v':
            diphthong = curr_char + next_char
            if diphthong in DIPHTHONGS:
                pairs_to_merge.append(j)
    
    for j in reversed(pairs_to_merge):
        if j + 1 < len(chars):
            merged_char = chars[j][1] + chars[j+1][1]
            chars[j][1] = merged_char
            del chars[j+1]

    return chars

def syllabify_word(word_sounds: list) -> list:
    """
    Делит слово (представленное списком звуков из функции sounder) на слоги.
    Основные правила: одна согласная идет в следующий слог, две согласные разделяются,
    группы согласных (например 'st', 'pl') целиком переходят в следующий слог.
    """
    if not word_sounds:
        return []

    vowel_indices = []
    for idx in range(len(word_sounds)):
        sound_type, sound_char = word_sounds[idx]
        if sound_type == 'v':
            vowel_indices.append(idx)

    if not vowel_indices:
        return []

    syllables = []
    total_vowels = len(vowel_indices)
    last_end_idx = 0

    for i in range(total_vowels):
        curr_vowel_idx = vowel_indices[i]
        start_idx = last_end_idx

        if i == total_vowels - 1:
            end_idx = len(word_sounds)
        else:
            next_vowel_idx = vowel_indices[i+1]
            consonants_between = word_sounds[curr_vowel_idx + 1 : next_vowel_idx]
            consonant_count = len(consonants_between)

            group_matched = False
            consonant_chars = []
            for sound in consonants_between:
                t, c = sound
                if t == 'c':
                    consonant_chars.append(c)
            consonant_str_between = ''.join(consonant_chars)

            for group in CONSONANT_GROUPS:
                if consonant_str_between == group:
                    group_matched = True
                    break
            if group_matched:
                end_idx = curr_vowel_idx + 1
            else:
                if consonant_count <= 1:
                    end_idx = curr_vowel_idx + 1
                else:
                    consonants_for_current = consonant_count - 1
                    end_idx = curr_vowel_idx + 1 + consonants_for_current
                    if end_idx > next_vowel_idx:
                        end_idx = curr_vowel_idx + 1

        last_end_idx = end_idx

        current_syllable = word_sounds[start_idx:end_idx]
        if current_syllable:
            syllable_tuple = []
            for sound in current_syllable:
                t, c = sound
                syllable_tuple.append((t, c))
            syllables.append(syllable_tuple)

    return syllables

def mark_syllable_type(syllable: str, syllable_sounds: list) -> str:
    """
    Определяет тип слога: открытый (открытый) или закрытый (закрытый).
    Открытый слог заканчивается гласной или дифтонгом.
    Закрытый слог заканчивается согласной.
    """
    if not syllable or not syllable_sounds:
        return "unknown"

    last_char = syllable[-1]
    is_diphthong = False
    pure_chars = []
    for c in syllable:
        pure_chars.append(LONG_MARK_MAP.get(c, c))
    pure_syllable = ''.join(pure_chars)

    for diphthong in DIPHTHONGS:
        if diphthong in pure_syllable and pure_syllable.endswith(diphthong[-1]):
            is_diphthong = True
            break
    if last_char in VOWELS or is_diphthong:
        return "открытый"
    last_sound_type = syllable_sounds[-1][0]
    if last_sound_type == 'c':
        return "закрытый"
    return "unknown"

def mark_syllable_length(syllable: str, syllable_sounds: list) -> str:
    """
    Определяет длину слога: долгий (длинный) или короткий (короткий).
    Правила для долгого слога: 1. Содержит знак долгой гласной. 2. Содержит дифтонг.
    3. Является закрытым слогом с двумя или более согласными после гласной (исключая некоторые комбинации).
    Правила для короткого слога: Является открытым слогом с короткой гласной, или закрытым слогом с одной согласной после гласной.
    """
    if not syllable or not syllable_sounds:
        return "короткий"

    for char in syllable:
        if char in LONG_MARK_MAP.keys():
            return "длинный"

    pure_chars_lower = []
    for c in syllable:
        pure_chars_lower.append(LONG_MARK_MAP.get(c.lower(), c.lower()))
    pure_syllable = ''.join(pure_chars_lower)

    for diphthong in DIPHTHONGS:
        if diphthong in pure_syllable:
            return "длинный"

    consonants_after_vowel = []
    vowel_found = False
    for sound_type, sound_char in syllable_sounds:
        if sound_type == 'v':
            vowel_found = True
            continue
        if vowel_found and sound_type == 'c':
            consonants_after_vowel.append(sound_char)

    stop_liquid_combinations = ['pr', 'tr', 'cr', 'br', 'dr', 'fr', 'gr',
                                'pl', 'cl', 'bl', 'fl', 'gl']
    consonant_count = len(consonants_after_vowel)

    if consonant_count >= 2:
        is_stop_liquid = False
        if consonant_count == 1:
            consonant_str = consonants_after_vowel[0]
            for combo in stop_liquid_combinations:
                if consonant_str == combo:
                    is_stop_liquid = True
                    break
        if not is_stop_liquid:
            return "длинный"

    return "короткий"

def syllable_to_str(syllable_sounds: list) -> str:
    """Преобразует список звуков слога обратно в строку."""
    if not syllable_sounds:
        return ""
    chars_in_syllable = []
    for s in syllable_sounds:
        chars_in_syllable.append(s[1])
    return ''.join(chars_in_syllable)

def add_accent_to_syllable(syllable_str: str) -> str:
    """Добавляет знак ударения ´ к гласной слога. Приоритет отдается первой гласной в дифтонге."""
    if not syllable_str:
        return syllable_str
    pure_vowels = ['a', 'e', 'i', 'o', 'u', 'y', 'ā', 'ē', 'ī', 'ō', 'ū', 'ȳ']
    diphthongs = DIPHTHONGS
    for diph in diphthongs:
        if diph in syllable_str:
            diph_index = syllable_str.find(diph)
            first_vowel = diph[0]
            accented_first_vowel = f'{first_vowel}´'
            accented_diph = accented_first_vowel + diph[1:]
            return syllable_str.replace(diph, accented_diph, 1)
    for vowel in pure_vowels:
        if vowel in syllable_str:
            vowel_index = syllable_str.find(vowel)
            accented_vowel = f'{vowel}´'
            return syllable_str[:vowel_index] + accented_vowel + syllable_str[vowel_index+len(vowel):]
    return syllable_str

def mark_accent_position(syllables_info: list) -> list:
    """
    Помечает положение ударения в слове по правилам латыни.
    Правила:
    1. Для двухсложных слов ударение находится на первом слоге.
    2. Для слов с более чем двумя слогами ударение находится на предпоследнем слоге, если он долгий.
    3. В противном случае ударение находится на третьем слоге с конца.
    """
    if not syllables_info:
        return []
    accented_syllables = []
    for s in syllables_info:
        accented_syllables.append(s.copy())
    
    syllable_count = len(accented_syllables)

    for syll in accented_syllables:
        syll['syllable_str_accented'] = syll['syllable_str']

    if syllable_count >= 2:
        if syllable_count == 2:
            accented_syllables[0]['syllable_str_accented'] = add_accent_to_syllable(accented_syllables[0]['syllable_str'])
        else:
            penult_index = syllable_count - 2
            penult_length = accented_syllables[penult_index]['length']
            if penult_length == "длинный":
                accented_syllables[penult_index]['syllable_str_accented'] = add_accent_to_syllable(accented_syllables[penult_index]['syllable_str'])
            else:
                antepenult_index = syllable_count - 3
                if antepenult_index >= 0:
                    accented_syllables[antepenult_index]['syllable_str_accented'] = add_accent_to_syllable(accented_syllables[antepenult_index]['syllable_str'])

    return accented_syllables

def worder(line: str) -> list:
    """
    Предобрабатывает входной текст: преобразует в нижний регистр, удаляет знаки препинания и цифры,
    заменяет 'x' на 'cs' и 'z' на 'ds', затем разделяет текст на список слов.
    """
    if not line:
        return []
    
    line = line.lower()
    extra_punctuation = '‘’“”«»'
    all_punctuation = string.punctuation + extra_punctuation
    translator = str.maketrans('', '', all_punctuation + string.digits)
    line = line.translate(translator)
    line = line.replace('x', 'cs').replace('z', 'ds')
    line = ' '.join(line.split())
    word_list = line.split() if line else []
    
    final_word_list = []
    for word in word_list:
        stripped_word = word.strip()
        if stripped_word:
            final_word_list.append(stripped_word)
    return final_word_list

def process_latin_text(input_text: str) -> list:
    """
    Основная функция обработки латинского текста.
    Выполняет следующие шаги последовательно: Предобработка текста -> Анализ фонем -> Деление на слоги ->
    Помечание атрибутов слогов (тип, длина) -> Помечание ударения.
    Возвращает список с информацией о каждом слове и его слогах.
    """
    result_list = []
    if not input_text:
        return result_list

    word_list = worder(input_text)
    for word in word_list:
        word_info = {
            "word": word,
            "syllables": []
        }
        word_sounds = sounder(word)
        if not word_sounds:
            result_list.append(word_info)
            continue
        syllables_sounds_list = syllabify_word(word_sounds)
        if not syllables_sounds_list:
            result_list.append(word_info)
            continue
        syllables_info = []
        for syllable_sounds in syllables_sounds_list:
            syllable_str = syllable_to_str(syllable_sounds)
            if not syllable_str:
                continue
            syllable_type = mark_syllable_type(syllable_str, syllable_sounds)
            syllable_length = mark_syllable_length(syllable_str, syllable_sounds)
            syllables_info.append({
                "syllable_str": syllable_str,
                "type": syllable_type,
                "length": syllable_length
            })
        accented_syllables_info = mark_accent_position(syllables_info)
        word_info["syllables"] = accented_syllables_info
        if word_info["syllables"]:
            result_list.append(word_info)

    return result_list