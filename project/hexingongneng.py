# Это инструмент для обработки латинского текста.
import string

# Определение групп согласных, которые рассматриваются как единое целое при делении на слоги
CONSONANT_GROUPS = [
    "bl", "br", "pl", "pr", "dr", "tr", "cl", "cr", "fr", "fl", "gr", "gl",
    "sp", "st", "sc", "ch", "ph", "th", "qu"
]

# Карта соответствия долгих гласных знаков коротким, используется для некоторых проверок
LONG_MARK_MAP = {
    'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u', 'ȳ': 'y',
    'Ā': 'A', 'Ē': 'E', 'Ī': 'I', 'Ō': 'O', 'Ū': 'U', 'Ȳ': 'Y'
}

# Обратная карта: короткие → долгие (для добавления ударения)
SHORT_TO_LONG_MAP = {v: k for k, v in LONG_MARK_MAP.items()}

# Определение дифтонгов (двойных гласных)
DIPHTHONGS = ['ae', 'oe', 'au', 'eu', 'ei', 'ui']

# Определение всех гласных (короткие + долгие)
SHORT_VOWELS = ['a', 'e', 'i', 'o', 'u', 'y']
LONG_VOWELS = ['ā', 'ē', 'ī', 'ō', 'ū', 'ȳ']
VOWELS = SHORT_VOWELS + LONG_VOWELS

# Определение всех согласных
CONSONANTS = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p',
              'q', 'r', 's', 't', 'v', 'w', 'x', 'z']

# Stop+Liquid组合 (не считаются как две согласные для длинного слога)
STOP_LIQUID = ['pr', 'tr', 'cr', 'br', 'dr', 'fr', 'gr', 'pl', 'cl', 'bl', 'fl', 'gl']

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
        # Обработка долгих гласных
        if char in LONG_VOWELS:
            chars.append(['v', char])
            i += 1
        # Обычные гласные
        elif char in SHORT_VOWELS:
            chars.append(['v', char])
            i += 1
        # Специальный случай 'u' после 'q'
        elif char == 'u':
            if i > 0 and word[i-1] == 'q':
                chars.append(['c', char])
            else:
                chars.append(['v', char])
            i += 1
        # Специальный случай 'i' (полугласный)
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
                prev_is_vowel = word[i-1] in VOWELS
                next_is_vowel = word[i+1] in VOWELS
                chars.append(['c', char] if (prev_is_vowel and next_is_vowel) else ['v', char])
                i += 1
        # Согласные и группы согласных
        else:
            matched = False
            # Проверка на группы согласных (2 символа)
            if i + 1 < word_len:
                two_char = word[i:i+2].lower()
                if two_char in CONSONANT_GROUPS:
                    chars.append(['c', word[i:i+2]])
                    i += 2
                    matched = True
            # Если группа не найдена - одиночная согласная
            if not matched:
                chars.append(['c', char])
                i += 1

    # Объединение дифтонгов
    pairs_to_merge = []
    for j in range(len(chars) - 1):
        curr_type, curr_char = chars[j]
        next_type, next_char = chars[j+1]
        if curr_type == 'v' and next_type == 'v':
            diphthong = curr_char.lower() + next_char.lower()
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
    Основные правила: 
    1. Одна согласная между гласными идет в следующий слог
    2. Две согласные разделяются (кроме групп согласных и stop+liquid)
    3. Группы согласных целиком переходят в следующий слог
    """
    if not word_sounds:
        return []

    # Найти индексы всех гласных
    vowel_indices = [idx for idx, (t, c) in enumerate(word_sounds) if t == 'v']
    if not vowel_indices:
        return []

    syllables = []
    total_vowels = len(vowel_indices)
    last_end_idx = 0

    for i in range(total_vowels):
        curr_vowel_idx = vowel_indices[i]
        start_idx = last_end_idx

        # Последний слог - берем все оставшиеся звуки
        if i == total_vowels - 1:
            end_idx = len(word_sounds)
        else:
            next_vowel_idx = vowel_indices[i+1]
            # Согласные между текущей и следующей гласной
            consonants_between = word_sounds[curr_vowel_idx + 1 : next_vowel_idx]
            consonant_count = len(consonants_between)

            # Проверка на группу согласных
            consonant_str = ''.join([c for t, c in consonants_between]).lower()
            is_consonant_group = consonant_str in CONSONANT_GROUPS or consonant_str in STOP_LIQUID

            if is_consonant_group or consonant_count <= 1:
                # Группа согласных или 1 согласная - все в следующий слог
                end_idx = curr_vowel_idx + 1
            else:
                # Две согласные - разделяем (первая в текущий, вторая в следующий)
                end_idx = curr_vowel_idx + 2

        last_end_idx = end_idx
        # Формируем слог
        current_syllable = word_sounds[start_idx:end_idx]
        if current_syllable:
            syllables.append(current_syllable)

    return syllables

def mark_syllable_type(syllable: str, syllable_sounds: list) -> str:
    """
    Определяет тип слога: открытый (открытый) или закрытый (закрытый).
    - Открытый: заканчивается гласной/дифтонгом
    - Закрытый: заканчивается согласной
    """
    if not syllable or not syllable_sounds:
        return "unknown"

    # Последний звук в слоге
    last_sound_type = syllable_sounds[-1][0]
    if last_sound_type == 'v':
        return "открытый"
    elif last_sound_type == 'c':
        return "закрытый"
    return "unknown"

def mark_syllable_length(syllable: str, syllable_sounds: list) -> str:
    """
    Определяет длину слога: долгий (длинный) или короткий (короткий).
    Правила:
    1. Долгий: содержит долгую гласную (ā, ē...) или дифтонг (ae, au...)
    2. Долгий: закрытый слог с двумя+ согласными после гласной (исключая stop+liquid)
    3. Короткий: остальные случаи
    """
    if not syllable or not syllable_sounds:
        return "короткий"

    # 1. Проверка на долгую гласную
    for char in syllable:
        if char in LONG_VOWELS:
            return "длинный"

    # 2. Проверка на дифтонг (приведем к нижнему регистру)
    pure_syllable = ''.join([LONG_MARK_MAP.get(c.lower(), c.lower()) for c in syllable])
    for diphthong in DIPHTHONGS:
        if diphthong in pure_syllable:
            return "длинный"

    # 3. Проверка на согласные после гласной
    consonants_after_vowel = []
    vowel_found = False
    for sound_type, sound_char in syllable_sounds:
        if sound_type == 'v':
            vowel_found = True
            continue
        if vowel_found and sound_type == 'c':
            consonants_after_vowel.append(sound_char.lower())

    # Объединим согласные для проверки групп
    consonant_str = ''.join(consonants_after_vowel)
    consonant_count = len(consonant_str) if consonant_str else 0

    # 4. Если после гласной ≥2 согласных (не stop+liquid) → долгий слог
    if consonant_count >= 2:
        if consonant_str not in STOP_LIQUID:
            return "длинный"

    # 5. Все остальные случаи → короткий
    return "короткий"

def syllable_to_str(syllable_sounds: list) -> str:
    """Преобразует список звуков слога обратно в строку."""
    if not syllable_sounds:
        return ""
    return ''.join([s[1] for s in syllable_sounds])

def add_accent_to_syllable(syllable_str: str) -> str:
    """
    Добавляет знак ударения ´ к гласной слога:
    1. Для дифтонгов - к первой гласной
    2. Для долгих гласных - к долгой гласной
    3. Для обычных гласных - к первой гласной
    """
    if not syllable_str:
        return syllable_str

    # Приведем к нижнему регистру для поиска (сохраним оригинал)
    syllable_lower = syllable_str.lower()
    
    # 1. Проверка на дифтонги
    for diph in DIPHTHONGS:
        if diph in syllable_lower:
            diph_idx = syllable_lower.find(diph)
            # Найдем позицию в оригинальной строке
            original_char = syllable_str[diph_idx]
            accented_char = f"{original_char}´"
            return syllable_str[:diph_idx] + accented_char + syllable_str[diph_idx+1:]
    
    # 2. Проверка на долгую гласную
    for long_vowel in LONG_VOWELS:
        if long_vowel in syllable_str:
            v_idx = syllable_str.find(long_vowel)
            accented_vowel = f"{long_vowel}´"
            return syllable_str[:v_idx] + accented_vowel + syllable_str[v_idx+1:]
    
    # 3. Проверка на обычную гласную
    for vowel in SHORT_VOWELS:
        if vowel in syllable_lower:
            v_idx = syllable_lower.find(vowel)
            original_char = syllable_str[v_idx]
            accented_char = f"{original_char}´"
            return syllable_str[:v_idx] + accented_char + syllable_str[v_idx+1:]
    
    return syllable_str

def mark_accent_position(syllables_info: list) -> list:
    """
    Помечает положение ударения в слове по правилам латыни:
    1. Двусложные: ударение на первом слоге
    2. Многосложные: 
       - Если предпоследний слог долгий → ударение на нем
       - Иначе → ударение на третьем слоге с конца
    """
    if not syllables_info:
        return []
    
    accented_syllables = [s.copy() for s in syllables_info]
    syllable_count = len(accented_syllables)
    
    if syllable_count < 2:
        # Односложные слова - ударение не нужно
        return accented_syllables
    
    # 2. Двусложные → ударение на первом
    if syllable_count == 2:
        accented_syllables[0]['syllable_str_accented'] = add_accent_to_syllable(
            accented_syllables[0]['syllable_str']
        )
    # 3. Многосложные
    else:
        penult_idx = syllable_count - 2  # предпоследний слог
        penult_length = accented_syllables[penult_idx]['length']
        
        if penult_length == "длинный":
            # Ударение на предпоследнем
            accented_syllables[penult_idx]['syllable_str_accented'] = add_accent_to_syllable(
                accented_syllables[penult_idx]['syllable_str']
            )
        else:
            # Ударение на третьем с конца (если существует)
            antepenult_idx = syllable_count - 3
            if antepenult_idx >= 0:
                accented_syllables[antepenult_idx]['syllable_str_accented'] = add_accent_to_syllable(
                    accented_syllables[antepenult_idx]['syllable_str']
                )
    
    # Заполним пустые значения оригинальным текстом
    for syl in accented_syllables:
        if 'syllable_str_accented' not in syl or not syl['syllable_str_accented']:
            syl['syllable_str_accented'] = syl['syllable_str']
    
    return accented_syllables

def worder(line: str) -> list:
    """
    Предобрабатывает входной текст:
    - Приводит к нижнему регистру
    - Удаляет знаки препинания и цифры
    - Заменяет 'x' на 'cs', 'z' на 'ds'
    - Разделяет на слова
    """
    if not line:
        return []
    
    line = line.lower()
    # Удаление препинания (стандартное + русское)
    extra_punctuation = '‘’“”«»—…'
    all_punctuation = string.punctuation + extra_punctuation
    translator = str.maketrans('', '', all_punctuation + string.digits)
    line = line.translate(translator)
    # Замена x/z
    line = line.replace('x', 'cs').replace('z', 'ds')
    # Разделение на слова
    return [word.strip() for word in line.split() if word.strip()]

def process_latin_text(input_text: str) -> list:
    """
    Основная функция обработки латинского текста:
    1. Предобработка → 2. Анализ фонем → 3. Деление на слоги → 
    4. Помечание типа/длины слогов → 5. Добавление ударения
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
        # Анализ фонем
        word_sounds = sounder(word)
        if not word_sounds:
            result_list.append(word_info)
            continue
        # Деление на слоги
        syllables_sounds_list = syllabify_word(word_sounds)
        if not syllables_sounds_list:
            result_list.append(word_info)
            continue
        # Анализ каждого слога
        syllables_info = []
        for syllable_sounds in syllables_sounds_list:
            syllable_str = syllable_to_str(syllable_sounds)
            if not syllable_str:
                continue
            # Определяем тип и длину
            syllable_type = mark_syllable_type(syllable_str, syllable_sounds)
            syllable_length = mark_syllable_length(syllable_str, syllable_sounds)
            syllables_info.append({
                "syllable_str": syllable_str,
                "type": syllable_type,
                "length": syllable_length,
                "syllable_str_accented": syllable_str  # По умолчанию без ударения
            })
        # Добавляем ударение
        accented_syllables_info = mark_accent_position(syllables_info)
        word_info["syllables"] = accented_syllables_info
        if word_info["syllables"]:
            result_list.append(word_info)

    return result_list

def analyze_statistics(processed_words):
    """
    Анализирует статистику:
    - Количество открытых/закрытых слогов
    - Количество долгих/коротких слогов
    - Статистика стоп (ритмических шагов)
    """
    # Базовая статистика
    open_count = 0
    closed_count = 0
    long_count = 0
    short_count = 0
    
    # Статистика стоп
    feet_counts = {}
    feet_details = []
    foot_names_map = {
        'SL': '抑扬格 (Iambus)',
        'LS': '扬抑格 (Trochee)',
        'LL': '扬扬格 (Spondee)',
        'SS': '抑抑格 (Pyrrhic)',
        'SLL': '抑抑扬格 (Anapest)',
        'LLS': '扬抑抑格 (Dactyl)',
        'LSL': '扬抑扬格 (Amphibrach)',
        'LLL': '三长格 (Molossus)',
        'SSS': '三短格 (Tribrach)'
    }

    for word_data in processed_words:
        word_text = word_data['word']
        syllables = word_data['syllables']
        
        # 1. Статистика типов и длин слогов
        for syl in syllables:
            # Тип слога
            if syl.get('type') == 'открытый':
                open_count += 1
            elif syl.get('type') == 'закрытый':
                closed_count += 1
            # Длина слога
            if syl.get('length') == 'длинный':
                long_count += 1
            elif syl.get('length') == 'короткий':
                short_count += 1
        
        # 2. Анализ стоп (двусилабные)
        # Игнорируем последний слог, если количество слогов нечетное
        max_idx = len(syllables) - 1 if len(syllables) % 2 != 0 else len(syllables)
        for i in range(0, max_idx - 1, 2):
            if i + 1 >= len(syllables):
                break
                
            s1 = syllables[i]
            s2 = syllables[i+1]
            
            # Текст слогов
            s1_text = s1.get('syllable_str', '?')
            s2_text = s2.get('syllable_str', '?')
            
            # Коды длины (L=длинный, S=короткий)
            len1 = 'L' if s1.get('length') == 'длинный' else 'S'
            len2 = 'L' if s2.get('length') == 'длинный' else 'S'
            foot_key = len1 + len2
            
            # Обновляем статистику
            feet_counts[foot_key] = feet_counts.get(foot_key, 0) + 1
            
            # Детали для таблицы
            len1_display = "длинный" if len1 == 'L' else "короткий"
            len2_display = "длинный" if len2 == 'L' else "короткий"
            feet_details.append({
                'word': word_text,
                'syllable_pair': f"{s1_text}-{s2_text}",
                'pattern': foot_key,
                'name': foot_names_map.get(foot_key, 'Неизвестно'),
                'analysis': f"1-й слог '{s1_text}' ({len1_display}) + 2-й слог '{s2_text}' ({len2_display})"
            })

    # Подготовка данных для визуализации
    total_words = len(processed_words)
    total_syllables = open_count + closed_count
    
    # Сортировка стоп по количеству
    sorted_feet = sorted(feet_counts.items(), key=lambda x: x[1], reverse=True)
    feet_labels = [item[0] for item in sorted_feet]
    feet_values = [item[1] for item in sorted_feet]
    
    return {
        'total_words': total_words,
        'total_syllables': total_syllables,
        'open_count': open_count,
        'closed_count': closed_count,
        'long_count': long_count,
        'short_count': short_count,
        'structure_labels': ['Открытые (Open)', 'Закрытые (Closed)'],
        'structure_values': [open_count, closed_count],
        'length_labels': ['Долгие (Long)', 'Краткие (Short)'],
        'length_values': [long_count, short_count],
        'feet_labels': feet_labels,
        'feet_values': feet_values,
        'feet_details': feet_details,
        'feet_names_map': foot_names_map
    }

# Пример использования (для тестирования)
if __name__ == "__main__":
    test_text = "arma virumque cano aere perennius"
    processed = process_latin_text(test_text)
    stats = analyze_statistics(processed)
    
    # Вывод результатов
    print("=== Обработка латинского текста ===")
    for word in processed:
        print(f"\nСлово: {word['word']}")
        for syl in word['syllables']:
            print(f"  Слог: {syl['syllable_str_accented']} | Тип: {syl['type']} | Длина: {syl['length']}")
    
    # Вывод статистики
    print("\n=== Статистика ===")
    print(f"Всего слов: {stats['total_words']} | Всего слогов: {stats['total_syllables']}")
    print(f"Открытые слоги: {stats['open_count']} | Закрытые: {stats['closed_count']}")
    print(f"Долгие слоги: {stats['long_count']} | Короткие: {stats['short_count']}")