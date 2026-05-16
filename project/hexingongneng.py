# 拉丁文本音节分析工具核心算法
# 功能：音节划分、开/闭音节判断、长/短音判断、重音规则、音步(стопа)统计
import string

# ====================== 全局常量定义 ======================
# 不可分割的辅音连缀组（划分音节时视为一个整体，不拆开）
CONSONANT_GROUPS = [
    "bl", "br", "pl", "pr", "dr", "tr", "cl", "cr", "fr", "fl", "gr", "gl",
    "sp", "st", "sc", "ch", "ph", "th", "qu"
]

# 长元音/短元音 → 普通元音映射（用于规范化判断）
# 同时支持长音符(macron)和短音符(breve)，统一转换为无变音符号的普通元音
LONG_MARK_MAP = {
    # 长音符 (macron)
    'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u', 'ȳ': 'y',
    'Ā': 'A', 'Ē': 'E', 'Ī': 'I', 'Ō': 'O', 'Ū': 'U', 'Ȳ': 'Y',
    # 短音符 (breve)
    'ă': 'a', 'ĕ': 'e', 'ĭ': 'i', 'ŏ': 'o', 'ŭ': 'u', 'y̆': 'y',
    'Ă': 'A', 'Ĕ': 'E', 'Ĭ': 'I', 'Ŏ': 'O', 'Ŭ': 'U', 'Y̆': 'Y'
}

# 普通元音 → 长元音映射（用于标重音）
# 只保留长元音映射，忽略短音符
SHORT_TO_LONG_MAP = {v: k for k, v in LONG_MARK_MAP.items() if len(k) == 1 and k in ['ā', 'ē', 'ī', 'ō', 'ū', 'ȳ']}

# 拉丁语双元音（不可拆分，整体为一个元音）
DIPHTHONGS = ['ae', 'oe', 'au', 'eu', 'ei', 'ui']

# 短元音、长元音、全部元音
SHORT_VOWELS = ['a', 'e', 'i', 'o', 'u', 'y']
LONG_VOWELS = ['ā', 'ē', 'ī', 'ō', 'ū', 'ȳ']
VOWELS = SHORT_VOWELS + LONG_VOWELS

# 拉丁语辅音字母
# 注：j和w是现代转写中使用的字母，古典拉丁语中无独立字母
# j对应辅音i（半元音/j/），w对应辅音v（半元音/w/）
CONSONANTS = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p',
        'q', 'r', 's', 't', 'v', 'w', 'x', 'z']

# 塞音+流音组合（位置在元音之间时，不强制前面音节变长）
# 这是位置长音规则中最重要的例外
STOP_LIQUID = ['pr', 'tr', 'cr', 'br', 'dr', 'fr', 'gr', 'pl', 'cl', 'bl', 'fl', 'gl']

# ====================== 音素分析 ======================
def sounder(word: str) -> list:
    """
    音素标记函数：把单词拆分成【元音/辅音】单元
    严格遵循古典拉丁语半元音判定规则（优先级从高到低）
    处理：双元音、辅音连缀、q-u 规则、i/j/u/v 半元音现象
    返回：列表，每个元素 = [类型(v/c), 字符]
    """
    if not word:
        return []
    
    chars = []
    word_len = len(word)
    i = 0

    while i < word_len:
        char = word[i]
        char_lower = char.lower()
        
        # ==============================================
        # 半元音判定最高优先级规则（永远成立）
        # ==============================================
        
        # 规则1：现代转写中的j永远是半元音（辅音）
        if char_lower == 'j':
            chars.append(['c', char])
            i += 1
            continue
        
        # 规则2：现代转写中的v永远是半元音（辅音）
        if char_lower == 'v':
            chars.append(['c', char])
            i += 1
            continue
        
        # 规则3：长元音ī永远是元音，无论位置如何
        if char == 'ī' or char == 'Ī':
            chars.append(['v', char])
            i += 1
            continue
        
        # 规则4：长元音ū永远是元音，无论位置如何
        if char == 'ū' or char == 'Ū':
            chars.append(['v', char])
            i += 1
            continue
        
        # ==============================================
        # 普通元音/辅音处理
        # ==============================================
        
        # 处理所有其他元音（a/e/o/y和短元音i/u）
        if char in VOWELS:
            # 单独处理短元音i的半元音情况
            if char_lower == 'i':
                if word_len == 1:
                    # 单音节词永远是元音
                    chars.append(['v', char])
                    i += 1
                    continue
                elif i == 0:
                    # 规则5：词首短元音i，后面紧跟元音→半元音（辅音）
                    if i + 1 < word_len and word[i+1] in VOWELS:
                        chars.append(['c', char])
                    else:
                        chars.append(['v', char])
                    i += 1
                    continue
                elif i == word_len - 1:
                    # 规则6：词尾i永远是元音
                    chars.append(['v', char])
                    i += 1
                    continue
                else:
                    # 规则7：词中短元音i，前后都是元音→半元音（辅音）
                    # 关键例外：如果i后面跟着a或e，则i是元音（解决-iae/-iei结尾问题）
                    prev_is_vowel = word[i-1] in VOWELS
                    next_is_vowel = word[i+1] in VOWELS
                    next_char = word[i+1].lower()

                    if prev_is_vowel and next_is_vowel and next_char not in ['a', 'e']:
                        chars.append(['c', char])
                    else:
                        chars.append(['v', char])
                    i += 1
                    continue
            
            # 单独处理短元音u的半元音情况
            elif char_lower == 'u':
                if i > 0 and word[i-1].lower() == 'q':
                    # 规则8：qu组合中的u永远是半元音（辅音）
                    chars.append(['c', char])
                    i += 1
                    continue
                elif word_len == 1:
                    # 单音节词永远是元音
                    chars.append(['v', char])
                    i += 1
                    continue
                elif i == word_len - 1:
                    # 规则9：词尾u永远是元音
                    chars.append(['v', char])
                    i += 1
                    continue
                else:
                    # 基础工具简化：词首和词中的u永远视为元音
                    # 现代转写中会用v明确表示半元音/w/
                    chars.append(['v', char])
                    i += 1
                    continue
            
            # 其他元音（a/e/o/y）直接标记为元音
            else:
                chars.append(['v', char])
                i += 1
                continue
        
        # ==============================================
        # 辅音处理
        # ==============================================
        
        # 优先匹配双辅音组，否则单个辅音
        matched = False
        if i + 1 < word_len:
            two_char = word[i:i+2].lower()
            if two_char in CONSONANT_GROUPS:
                chars.append(['c', word[i:i+2]])
                i += 2
                matched = True
        if not matched:
            chars.append(['c', char])
            i += 1

    # ==============================================
    # 双元音合并（两个相邻元音如果是合法双元音，合并为一个元音单元）
    # ==============================================
    pairs_to_merge = []
    for j in range(len(chars) - 1):
        curr_type, curr_char = chars[j]
        next_type, next_char = chars[j+1]
        if curr_type == 'v' and next_type == 'v':
            diphthong = curr_char.lower() + next_char.lower()
            if diphthong in DIPHTHONGS:
                pairs_to_merge.append(j)
    
    # 倒序删除，防止索引错乱
    for j in reversed(pairs_to_merge):
        if j + 1 < len(chars):
            merged_char = chars[j][1] + chars[j+1][1]
            chars[j][1] = merged_char
            del chars[j+1]

    return chars
# ====================== 音节划分核心 ======================
def syllabify_word(word_sounds: list) -> list:
    """
    音节划分函数（拉丁语经典规则）
    1. 元音之间一个辅音 → 归后一音节
    2. 两个辅音 → 前后各一
    3. 辅音组/塞音流音组 → 整体归后一音节
    返回：音节列表（每个音节是音素列表）
    """
    if not word_sounds:
        return []

    # 提取所有元音的位置（每个音节必须有且只有一个元音核心）
    vowel_indices = [idx for idx, (t, c) in enumerate(word_sounds) if t == 'v']
    if not vowel_indices:
        return []

    syllables = []
    total_vowels = len(vowel_indices)
    last_end_idx = 0

    for i in range(total_vowels):
        curr_vowel_idx = vowel_indices[i]
        start_idx = last_end_idx

        # 最后一个音节：直接取剩下所有
        if i == total_vowels - 1:
            end_idx = len(word_sounds)
        else:
            next_vowel_idx = vowel_indices[i+1]
            consonants_between = word_sounds[curr_vowel_idx + 1 : next_vowel_idx]
            consonant_count = len(consonants_between)

            # 拼接成字符串，判断是否是辅音组
            consonant_str = ''.join([c for t, c in consonants_between]).lower()
            is_consonant_group = consonant_str in CONSONANT_GROUPS or consonant_str in STOP_LIQUID

            # 1个辅音 或 辅音组 → 整个归下一个音节
            if is_consonant_group or consonant_count <= 1:
                end_idx = curr_vowel_idx + 1
            # 两个及以上非组辅音 → 拆分，前一个归当前音节
            else:
                end_idx = curr_vowel_idx + 2

        last_end_idx = end_idx
        current_syllable = word_sounds[start_idx:end_idx]
        if current_syllable:
            syllables.append(current_syllable)

    return syllables

# ====================== 开/闭音节判断 ======================
def mark_syllable_type(syllable: str, syllable_sounds: list) -> str:
    """
    判断音节类型：
    以元音结尾 → 开音节（открытый）
    以辅音结尾 → 闭音节（закрытый）
    """
    if not syllable or not syllable_sounds:
        return "unknown"

    last_sound_type = syllable_sounds[-1][0]
    if last_sound_type == 'v':
        return "открытый"
    elif last_sound_type == 'c':
        return "закрытый"
    return "unknown"

# ====================== 长/短音判断 ======================
def mark_syllable_length(syllable: str, syllable_sounds: list) -> str:
    """
    音节音长规则（拉丁语核心）
    1. 自带长元音 → 长音
    2. 双元音 → 长音
    3. 元音后有 ≥2 个辅音（非 STOP_LIQUID）→ 长音（positione）
    其余 → 短音
    """
    if not syllable or not syllable_sounds:
        return "короткий"

    # 规则1：长元音 → 长音
    for char in syllable:
        if char in LONG_VOWELS:
            return "длинный"

    # 规则2：双元音 → 长音
    pure_syllable = ''.join([LONG_MARK_MAP.get(c.lower(), c.lower()) for c in syllable])
    for diphthong in DIPHTHONGS:
        if diphthong in pure_syllable:
            return "длинный"

    # 收集元音后面的辅音
    consonants_after_vowel = []
    vowel_found = False
    for sound_type, sound_char in syllable_sounds:
        if sound_type == 'v':
            vowel_found = True
            continue
        if vowel_found and sound_type == 'c':
            consonants_after_vowel.append(sound_char.lower())

    consonant_str = ''.join(consonants_after_vowel)
    consonant_count = len(consonant_str)

    # 规则3：两个及以上辅音（非塞音+流音）→ 长音
    if consonant_count >= 2:
        if consonant_str not in STOP_LIQUID:
            return "длинный"

    # 其余都算短音
    return "короткий"

# ====================== 工具函数 ======================
def syllable_to_str(syllable_sounds: list) -> str:
    """把音素结构转回普通字符串"""
    if not syllable_sounds:
        return ""
    return ''.join([s[1] for s in syllable_sounds])

def add_accent_to_syllable(syllable_str: str) -> str:
    """给音节的元音加上重音符号 ´"""
    if not syllable_str:
        return syllable_str

    syllable_lower = syllable_str.lower()
    
    # 重音加在双元音第一个字母
    for diph in DIPHTHONGS:
        if diph in syllable_lower:
            diph_idx = syllable_lower.find(diph)
            original_char = syllable_str[diph_idx]
            accented_char = f"{original_char}´"
            return syllable_str[:diph_idx] + accented_char + syllable_str[diph_idx+1:]
    
    # 长元音 → 加重音
    for long_vowel in LONG_VOWELS:
        if long_vowel in syllable_str:
            v_idx = syllable_str.find(long_vowel)
            accented_vowel = f"{long_vowel}´"
            return syllable_str[:v_idx] + accented_vowel + syllable_str[v_idx+1:]
    
    # 短元音 → 加重音
    for vowel in SHORT_VOWELS:
        if vowel in syllable_lower:
            v_idx = syllable_lower.find(vowel)
            original_char = syllable_str[v_idx]
            accented_char = f"{original_char}´"
            return syllable_str[:v_idx] + accented_char + syllable_str[v_idx+1:]
    
    return syllable_str

# ====================== 拉丁语重音规则 ======================
def mark_accent_position(syllables_info: list) -> list:
    """
    拉丁语重音规则：
    1. 双音节词 → 重音在第一音节
    2. 多音节词：
    - 倒数第二音节长 → 重音在它
    - 倒数第二音节短 → 重音在倒数第三音节
    """
    if not syllables_info:
        return []
    
    accented_syllables = [s.copy() for s in syllables_info]
    syllable_count = len(accented_syllables)
    
    if syllable_count < 2:
        return accented_syllables
    
    # 双音节词
    if syllable_count == 2:
        accented_syllables[0]['syllable_str_accented'] = add_accent_to_syllable(
            accented_syllables[0]['syllable_str']
        )
    # 多音节词
    else:
        penult_idx = syllable_count - 2
        penult_length = accented_syllables[penult_idx]['length']
        
        if penult_length == "длинный":
            # 倒数第二长 → 重音在这
            accented_syllables[penult_idx]['syllable_str_accented'] = add_accent_to_syllable(
                accented_syllables[penult_idx]['syllable_str']
            )
        else:
            # 否则 → 倒数第三
            antepenult_idx = syllable_count - 3
            if antepenult_idx >= 0:
                accented_syllables[antepenult_idx]['syllable_str_accented'] = add_accent_to_syllable(
                    accented_syllables[antepenult_idx]['syllable_str']
                )
    
    # 未标重音的保持原字符串
    for syl in accented_syllables:
        if 'syllable_str_accented' not in syl or not syl['syllable_str_accented']:
            syl['syllable_str_accented'] = syl['syllable_str']
    
    return accented_syllables

# ====================== 文本预处理 ======================
def worder(line: str) -> list:
    """
    文本清洗：
    - 转小写
    - 去标点、数字
    - x→cs，z→ds（拉丁语音变规则）
    - 分割成单词列表
    """
    if not line:
        return []
    
    line = line.lower()
    extra_punctuation = '‘’“”«»—…'
    all_punctuation = string.punctuation + extra_punctuation
    translator = str.maketrans('', '', all_punctuation + string.digits)
    line = line.translate(translator)
    line = line.replace('x', 'cs').replace('z', 'ds')
    return [word.strip() for word in line.split() if word.strip()]

# ====================== 主处理函数 ======================
def process_latin_text(input_text: str) -> list:
    """
    顶层处理流程（整个工具的核心 pipeline）
    1. 文本清洗 → 2. 音素分析 → 3. 音节划分
    → 4. 开/闭、长/短标记 → 5. 重音标记
    返回：每个单词 + 音节详情
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
        # 音素化
        word_sounds = sounder(word)
        if not word_sounds:
            result_list.append(word_info)
            continue
        # 划分音节
        syllables_sounds_list = syllabify_word(word_sounds)
        if not syllables_sounds_list:
            result_list.append(word_info)
            continue
        # 分析每个音节
        syllables_info = []
        for syllable_sounds in syllables_sounds_list:
            syllable_str = syllable_to_str(syllable_sounds)
            if not syllable_str:
                continue
            # 类型、音长
            syllable_type = mark_syllable_type(syllable_str, syllable_sounds)
            syllable_length = mark_syllable_length(syllable_str, syllable_sounds)
            syllables_info.append({
                "syllable_str": syllable_str,
                "type": syllable_type,
                "length": syllable_length,
                "syllable_str_accented": syllable_str
            })
        # 标注重音
        accented_syllables_info = mark_accent_position(syllables_info)
        word_info["syllables"] = accented_syllables_info
        if word_info["syllables"]:
            result_list.append(word_info)

    return result_list

# ====================== 统计与图表数据（修复多音节+兼容前端所有字段） ======================
def analyze_statistics(processed_words):
    """
    统计功能（用于前端图表展示）
    - 开/闭音节数量
    - 长/短音节数量
    - 音步类型统计（双音节音步）
    - 输出图表所需的标签与数值
    """
    open_count = 0
    closed_count = 0
    long_count = 0
    short_count = 0
    
    # 音步统计
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
        
        # 🔥 修复1：生成【完整音节划分】（所有音节用-连接，不截断）
        full_syllable_str = "-".join([syl['syllable_str'] for syl in syllables])
        
        # 统计开闭、长短（无修改）
        for syl in syllables:
            if syl.get('type') == 'открытый':
                open_count += 1
            elif syl.get('type') == 'закрытый':
                closed_count += 1

            if syl.get('length') == 'длинный':
                long_count += 1
            elif syl.get('length') == 'короткий':
                short_count += 1
        
        # 🔥 修复2：音步仍两两分组，音节划分完整显示
        for i in range(0, len(syllables) - 1, 2):
            if i + 1 >= len(syllables):
                break
                
            s1 = syllables[i]
            s2 = syllables[i+1]
            
            len1 = 'L' if s1.get('length') == 'длинный' else 'S'
            len2 = 'L' if s2.get('length') == 'длинный' else 'S'
            foot_key = len1 + len2
            
            feet_counts[foot_key] = feet_counts.get(foot_key, 0) + 1
            
            # 🔥 核心修复：补全前端需要的 ALL 字段，解决所有UndefinedError
            foot_name = foot_names_map.get(foot_key, 'Неизвестно')
            feet_details.append({
                'word': word_text,
                'syllable_pair': full_syllable_str,
                'pattern': foot_key,
                'name': foot_name,
                'name_local': foot_name,  # ✅ 前端需要name_local，直接赋值
                'oc': s1['type'] + ' + ' + s2['type'],  # ✅ 前端需要oc（开闭音节）
                'ls': s1['length'] + ' + ' + s2['length'],  # ✅ 前端需要ls（音长）
                'analysis': f"1-й слог '{s1['syllable_str']}' ({s1['length']}) + 2-й слог '{s2['syllable_str']}' ({s2['length']})"
            })

    total_words = len(processed_words)
    total_syllables = open_count + closed_count
    
    # 按出现频率排序
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
# ====================== 测试 ======================
if __name__ == "__main__":
    test_text = "arma virumque cano aere perennius"
    processed = process_latin_text(test_text)
    stats = analyze_statistics(processed)
    
    print("=== 拉丁文本音节分析结果 ===")
    for word in processed:
        print(f"\n单词：{word['word']}")
        for syl in word['syllables']:
            print(f"  音节：{syl['syllable_str_accented']} | 类型：{syl['type']} | 长短：{syl['length']}")
    
    print("\n=== 统计信息 ===")
    print(f"总单词数：{stats['total_words']} | 总音节数：{stats['total_syllables']}")
    print(f"开音节：{stats['open_count']} | 闭音节：{stats['closed_count']}")
    print(f"长音节：{stats['long_count']} | 短音节：{stats['short_count']}")
