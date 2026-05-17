#拉丁文本音节分析工具核心算法
#功能：音节划分、开/闭音节判断、长/短音判断、重音规则、音步(стопа)统计
#新增：散文/诗歌双模式切换，诗歌支持省音、连续音流、通用音步划分
import string

# ====================== 全局常量定义 ======================
# 不可分割的辅音连缀组（划分音节时视为一个整体，绝对不拆开）
# 权威来源：Allen & Greenough §11, Wheelock's Latin 7th Edition
CONSONANT_GROUPS = [
    # 塞音+流音（唯一在元音之间可以整体归后的组合）
    "bl", "br", "pl", "pr", "dr", "tr", "cl", "cr", "fr", "fl", "gr", "gl",
    # 送气塞音（古典拉丁语中是单个音素）
    "ch", "ph", "th",
    # qu（永远作为一个辅音音素/kʷ/）
    "qu"
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
# 这是位置长音规则中唯一的例外
# 权威来源：Dickinson College Commentaries, Allen & Greenough §603
STOP_LIQUID = [
    'pr', 'tr', 'cr', 'br', 'dr', 'fr', 'gr',
    'pl', 'cl', 'bl', 'fl', 'gl',
    'chl', 'chr', 'phl', 'phr', 'thl', 'thr'
]

# 特殊辅音计数：x=cs, z=ds，每个都算2个辅音
# 权威来源：Allen & Greenough §604
SPECIAL_CONSONANTS = {'x': 2, 'z': 2}

# 忽略的辅音：h只是送气符号，不算真正的辅音，不能关闭音节
IGNORED_CONSONANTS = {'h'}

# ====================== 新增：诗歌分析专用常量 ======================
# 你的音步名称映射表（完全采用）
FOOT_NAMES_MAP = {
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

# 音步长度映射
FOOT_LENGTHS = {k: len(k) for k in FOOT_NAMES_MAP.keys()}


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


# ====================== 🌟 修正后的长/短音判断函数（严格按规则A/B/C） ======================
def mark_syllable_length(syllable: str, syllable_sounds: list, is_last_syllable: bool = False) -> str:
    """
    完全符合古典拉丁语标准的音节音长判断
    权威来源：Allen & Greenough's Latin Grammar §600-612, Dickinson College Commentaries
    核心规则（优先级从高到低）：
    А. 自然长音 (Natura Longa)
    Б. 位置长音 (Positione Longa)
    В. 短音 (Brevis)
    """
    if not syllable or not syllable_sounds:
        return "короткий"

    # А. 自然长音 (Natura Longa)
    # 1. 包含长元音（ā, ē, ī, ō, ū, ȳ）→ 长
    for char in syllable:
        if char in LONG_VOWELS:
            return "длинный"
            
    # 2. 包含双元音（ae, au, oe, ei, eu, ui）→ 长
    pure_syllable = ''.join([LONG_MARK_MAP.get(c, c.lower()) for c in syllable])
    for diphthong in DIPHTHONGS:
        if diphthong in pure_syllable:
            if pure_syllable.find(diphthong) != -1:
                return "длинный"

    # 收集元音后面的所有有效辅音（忽略 h）
    consonants_after_vowel = []
    vowel_found = False
    for sound_type, sound_char in syllable_sounds:
        if sound_type == 'v':
            vowel_found = True
            continue
        if vowel_found and sound_type == 'c':
            c_low = sound_char.lower()
            if c_low != 'h':
                consonants_after_vowel.append(c_low)

    if not consonants_after_vowel:
        return "короткий"

    # Б. 位置长音 (Positione Longa)
    # 计算有效辅音权重
    eff_count = 0
    for c in consonants_after_vowel:
        if c in ('x', 'z'):
            eff_count += 2  # x, z = 2辅音
        elif c in ('ch', 'th', 'ph'):
            eff_count += 2  # 送气塞音 = 2辅音
        elif c == 'qu':
            eff_count += 1  # qu 整体算 1
        elif c in STOP_LIQUID:
            eff_count += 1  # 爆破音+流音 = 1（不延长）
        else:
            eff_count += 1  # 普通辅音 = 1

    # Б.4 规则：词尾闭音节（-m, -n, -s, -t, -x, -d, -l, -r 等）→ 长
    if is_last_syllable and eff_count >= 1:
        return "длинный"

    # Б.1-3 规则：有效辅音数 >= 2 → 长
    if eff_count >= 2:
        return "длинный"

    # В. 短音 (Brevis)
    # 1个或0个有效辅音（且非词尾闭音节） → 短
    return "короткий"


# ====================== 工具函数 ======================
def syllable_to_str(syllable_sounds: list) -> str:
    """把音素结构转回普通字符串"""
    if not syllable_sounds:
        return ""
    return ''.join([s[1] for s in syllable_sounds])

def add_accent_to_syllable(syllable_str: str) -> str:
    """
    给音节的元音加上正确的拉丁语重音符号（锐音符 ´ 叠加在字母上方）
    权威来源：Allen & Greenough §12, Wheelock's Latin 7th Edition
    规则：
    1. 双元音：重音加在第一个元音上
    2. 单元音：重音加在唯一的元音上（无论长短）
    3. 重音符号使用Unicode组合锐音符 U+0301，正确显示在字母上方
    """
    if not syllable_str:
        return syllable_str
    
    syllable_lower = syllable_str.lower()

    # 规则1：优先处理双元音（重音加在第一个元音上）
    for diph in DIPHTHONGS:
        diph_idx = syllable_lower.find(diph)
        if diph_idx != -1:
            if (syllable_lower[diph_idx] in VOWELS and 
                syllable_lower[diph_idx+1] in VOWELS):
                original_char = syllable_str[diph_idx]
                accented_char = f"{original_char}\u0301"
                return syllable_str[:diph_idx] + accented_char + syllable_str[diph_idx+1:]

    # 规则2：处理单元音（按出现顺序找到第一个元音）
    for i, char in enumerate(syllable_str):
        char_lower = char.lower()
        if char_lower in VOWELS:
            accented_char = f"{char}\u0301"
            return syllable_str[:i] + accented_char + syllable_str[i+1:]

    # 没有找到元音（理论上不可能）
    return syllable_str


# ====================== 修正后的拉丁语重音规则函数 ======================
def mark_accent_position(syllables_info: list) -> list:
    """
    完全符合古典拉丁语标准的重音位置判断
    权威来源：Allen & Greenough §230-238, Wheelock's Latin 7th Edition
    核心规则：
    1. 单音节词：无重音
    2. 双音节词：重音永远在第一音节
    3. 多音节词：
       - 倒数第二音节长 → 重音在倒数第二音节
       - 倒数第二音节短 → 重音在倒数第三音节

    重要例外（附着词）：
    当单词以附着词(-que, -ve, -ne, -ce, -met)结尾时，
    重音强制移到整个组合的倒数第二音节，无论其长度如何
    """
    if not syllables_info:
        return []
    
    accented_syllables = [s.copy() for s in syllables_info]
    syllable_count = len(accented_syllables)

    # 单音节词：无重音
    if syllable_count < 2:
        for syl in accented_syllables:
            syl['is_accented'] = False
            syl['syllable_str_accented'] = syl['syllable_str']
        return accented_syllables

    # 检查是否以附着词结尾
    ENCLITICS = {'que', 've', 'ne', 'ce', 'met'}
    last_syllable_str = accented_syllables[-1]['syllable_str'].lower()
    has_enclitic = last_syllable_str in ENCLITICS

    accent_idx = -1

    if has_enclitic and syllable_count >= 2:
        # 附着词规则：重音强制在倒数第二音节
        accent_idx = syllable_count - 2
    elif syllable_count == 2:
        # 双音节词：重音在第一音节
        accent_idx = 0
    else:
        # 多音节词：正常规则
        penult_idx = syllable_count - 2
        penult_length = accented_syllables[penult_idx]['length']
        
        if penult_length == "длинный":
            accent_idx = penult_idx
        else:
            antepenult_idx = syllable_count - 3
            if antepenult_idx >= 0:
                accent_idx = antepenult_idx

    # 标记重音音节
    for i, syl in enumerate(accented_syllables):
        if i == accent_idx:
            syl['is_accented'] = True
            syl['syllable_str_accented'] = add_accent_to_syllable(syl['syllable_str'])
        else:
            syl['is_accented'] = False
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


# ====================== 新增：诗歌专用预处理（生成连续音流） ======================
def poetry_preprocess(text: str) -> str:
    """
    诗歌文本预处理：生成完全连续的字母流
    - 转小写
    - 移除所有标点、数字和空格
    - x→cs，z→ds（内部发音转换）
    """
    if not text:
        return ""
    text = text.lower()
    extra_punctuation = '‘’“”«»—… \t\n\r'
    all_punctuation = string.punctuation + extra_punctuation + string.digits
    translator = str.maketrans('', '', all_punctuation)
    text = text.translate(translator)
    text = text.replace('x', 'cs').replace('z', 'ds')
    
    return text


# ====================== 新增：诗歌核心-省音处理（Elision） ======================
def apply_elision(text: str) -> str:
    """
    应用拉丁语诗歌完整省音规则（文本级别处理，实现真正的字母合并）
    权威来源：Allen & Greenough §612-620
    规则：
    1. 以m结尾的单词 + 元音/h开头的单词 → m省略，两词合并
    2. 以元音结尾的单词 + 元音/h开头的单词 → 前一个元音省略，两词合并
    3. 例外：et不省音，单音节词不省音
    """
    if not text:
        return ""
    
    words = text.split()
    processed_words = []
    i = 0
    n = len(words)

    while i < n:
        current_word = words[i]
        
        # 例外：et永远不省音
        if current_word == 'et':
            processed_words.append(current_word)
            i += 1
            continue
        
        # 例外：单音节词不省音
        if len(current_word) == 1:
            processed_words.append(current_word)
            i += 1
            continue
        
        if i < n - 1:
            next_word = words[i+1]
            next_first_char = next_word[0]
            
            # 规则1：m尾省音（最常见）
            if current_word.endswith('m') and (next_first_char in VOWELS or next_first_char == 'h'):
                merged_word = current_word[:-1] + next_word
                processed_words.append(merged_word)
                i += 2
                continue
            
            # 规则2：元音尾省音
            if current_word[-1] in VOWELS and (next_first_char in VOWELS or next_first_char == 'h'):
                merged_word = current_word[:-1] + next_word
                processed_words.append(merged_word)
                i += 2
                continue
        
        # 无省音，正常添加
        processed_words.append(current_word)
        i += 1

    # 合并成完全连续的字母流
    return ''.join(processed_words)


# ====================== 新增：诗歌核心-连续音流音节划分 ======================
def syllabify_continuous(sounds: list) -> list:
    """
    将连续的音素列表整体划分为音节
    完全忽略单词边界，按照拉丁语音节划分规则处理
    """
    if not sounds:
        return []
    
    vowel_indices = [idx for idx, (t, c) in enumerate(sounds) if t == 'v']
    
    if len(vowel_indices) == 0:
        return [sounds]

    syllables = []
    last_end_idx = 0

    for i in range(len(vowel_indices)):
        curr_vowel_idx = vowel_indices[i]
        start_idx = last_end_idx
        
        if i == len(vowel_indices) - 1:
            end_idx = len(sounds)
        else:
            next_vowel_idx = vowel_indices[i+1]
            consonants_between = sounds[curr_vowel_idx + 1 : next_vowel_idx]
            consonant_count = len(consonants_between)
            
            consonant_str = ''.join([c for t, c in consonants_between]).lower()
            is_consonant_group = consonant_str in CONSONANT_GROUPS or consonant_str in STOP_LIQUID
            
            if is_consonant_group or consonant_count <= 1:
                end_idx = curr_vowel_idx + 1
            else:
                end_idx = curr_vowel_idx + 2
        
        last_end_idx = end_idx
        current_syllable = sounds[start_idx:end_idx]
        if current_syllable:
            syllables.append(current_syllable)

    return syllables


# ====================== 新增：通用音步匹配引擎（基于你的SL体系） ======================
def match_foot(syllables_info: list, start_pos: int, allowed_feet: list = None) -> tuple:
    """
    从指定位置开始，匹配允许的音步模式
    返回：(匹配到的音步模式, 匹配的音节数量)
    """
    if allowed_feet is None:
        allowed_feet = list(FOOT_NAMES_MAP.keys())
        
    if start_pos >= len(syllables_info):
        return (None, 0)

    # 生成从当前位置开始的音长序列
    length_sequence = []
    for i in range(start_pos, min(start_pos + 3, len(syllables_info))):
        length_sequence.append('L' if syllables_info[i]['length'] == 'длинный' else 'S')

    length_str = ''.join(length_sequence)

    # 按音步长度从长到短匹配（优先匹配更长的音步）
    for foot_length in [3, 2, 1]:
        if len(length_str) < foot_length:
            continue
        candidate = length_str[:foot_length]
        if candidate in allowed_feet:
            return (candidate, foot_length)

    # 默认匹配2个音节作为扬扬格
    if len(length_str) >= 2:
        return ('LL', 2)
    return ('L', 1)


# ====================== 主处理函数（新增mode参数，散文/诗歌通用） ======================
def process_latin_text(input_text: str, mode: str = "prose") -> list:
    """
    顶层处理流程（散文/诗歌通用）
    mode: "prose"（散文，默认）或 "poetry"（诗歌）
    散文模式：按单词处理，标注重音
    诗歌模式：生成连续音流，应用省音，整体划分音节和音步
    """
    result_list = []
    if not input_text:
        return result_list

    if mode == "prose":
        # 散文模式：完全保留你原有的处理逻辑
        word_list = worder(input_text)
        for word in word_list:
            word_info = {
                "word": word,
                "mode": "prose",
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
            syllable_count = len(syllables_sounds_list)
            for i, syllable_sounds in enumerate(syllables_sounds_list):
                syllable_str = syllable_to_str(syllable_sounds)
                if not syllable_str:
                    continue
                # 判断是否是最后一个音节
                is_last_syllable = (i == syllable_count - 1)
                # 类型、音长
                syllable_type = mark_syllable_type(syllable_str, syllable_sounds)
                syllable_length = mark_syllable_length(syllable_str, syllable_sounds, is_last_syllable)
                syllables_info.append({
                    "syllable_str": syllable_str,
                    "type": syllable_type,
                    "length": syllable_length,
                    "is_last_syllable": is_last_syllable,
                    "syllable_str_accented": syllable_str
                })
            # 标注重音（仅散文模式）
            accented_syllables_info = mark_accent_position(syllables_info)
            word_info["syllables"] = accented_syllables_info
            if word_info["syllables"]:
                result_list.append(word_info)

    elif mode == "poetry":
        # 诗歌模式：连续音流处理
        line_info = {
            "line": input_text,
            "mode": "poetry",
            "continuous_text": "",
            "syllables": [],
            "feet": []
        }
        
        # 1. 生成连续音流
        continuous_text = poetry_preprocess(input_text)
        line_info["continuous_text"] = continuous_text
        
        # 2. 音素化
        sounds = sounder(continuous_text)
        if not sounds:
            result_list.append(line_info)
            return result_list
        
        # 3. 应用省音
        sounds_after_elision = apply_elision(sounds)
        
        # 4. 整体划分音节
        syllables_sounds_list = syllabify_continuous(sounds_after_elision)
        if not syllables_sounds_list:
            result_list.append(line_info)
            return result_list
        
        # 5. 分析每个音节
        syllables_info = []
        syllable_count = len(syllables_sounds_list)
        for i, syllable_sounds in enumerate(syllables_sounds_list):
            syllable_str = syllable_to_str(syllable_sounds)
            if not syllable_str:
                continue
            is_last_syllable = (i == syllable_count - 1)
            syllable_type = mark_syllable_type(syllable_str, syllable_sounds)
            syllable_length = mark_syllable_length(syllable_str, syllable_sounds, is_last_syllable)
            length_symbol = "⏒" if syllable_length == "длинный" else "⏑"
            
            syllables_info.append({
                "syllable_str": syllable_str,
                "type": syllable_type,
                "length": syllable_length,
                "length_symbol": length_symbol,
                "is_last_syllable": is_last_syllable
            })
        
        line_info["syllables"] = syllables_info
        
        # 6. 自动划分音步（通用模式）
        feet = []
        current_pos = 0
        while current_pos < len(syllables_info):
            foot_pattern, foot_length = match_foot(syllables_info, current_pos)
            foot_syllables = syllables_info[current_pos:current_pos + foot_length]
            
            feet.append({
                "pattern": foot_pattern,
                "name": FOOT_NAMES_MAP.get(foot_pattern, "未知音步"),
                "syllables": foot_syllables,
                "length_symbols": ''.join([s["length_symbol"] for s in foot_syllables])
            })
            
            current_pos += foot_length
        
        line_info["feet"] = feet
        result_list.append(line_info)

    return result_list


# ====================== 统计与图表数据（新增诗歌模式支持） ======================
def analyze_statistics(processed_results):
    """
    统计功能（散文/诗歌通用）
    - 开/闭音节数量
    - 长/短音节数量
    - 音步类型统计
    - 输出图表所需的标签与数值
    """
    open_count = 0
    closed_count = 0
    long_count = 0
    short_count = 0
    feet_counts = {}
    feet_details = []
    
    # Новая таблица для prose режима: одно слово - одна строка
    word_table = []

    for result in processed_results:
        if result.get("mode") == "prose":
            # 散文模式统计（完全保留你原有的逻辑）
            word_text = result['word']
            syllables = result['syllables']
            
            full_syllable_str = "-".join([syl['syllable_str'] for syl in syllables])
            
            oc_list = []
            ls_list = []
            
            for syl in syllables:
                if syl.get('type') == 'открытый':
                    open_count += 1
                    oc_list.append('открытый')
                elif syl.get('type') == 'закрытый':
                    closed_count += 1
                    oc_list.append('закрытый')

                if syl.get('length') == 'длинный':
                    long_count += 1
                    ls_list.append('длинный')
                elif syl.get('length') == 'короткий':
                    short_count += 1
                    ls_list.append('короткий')
            
            # Добавляем слово в таблицу анализа (ОДНА СТРОКА НА СЛОВО)
            word_table.append({
                'word': word_text,
                'syllables_full': full_syllable_str,
                'oc_raw': oc_list,
                'ls_raw': ls_list
            })
            
            # 散文模式音步统计（两两分组）
            for i in range(0, len(syllables) - 1, 2):
                if i + 1 >= len(syllables):
                    break
                    
                s1 = syllables[i]
                s2 = syllables[i+1]
                
                len1 = 'L' if s1.get('length') == 'длинный' else 'S'
                len2 = 'L' if s2.get('length') == 'длинный' else 'S'
                foot_key = len1 + len2
                
                feet_counts[foot_key] = feet_counts.get(foot_key, 0) + 1
                
                foot_name = FOOT_NAMES_MAP.get(foot_key, 'Неизвестно')
                feet_details.append({
                    'word': word_text,
                    'syllable_pair': full_syllable_str,
                    'pattern': foot_key,
                    'name': foot_name,
                    'name_local': foot_name,
                    'oc': s1['type'] + ' + ' + s2['type'],
                    'ls': s1['length'] + ' + ' + s2['length'],
                    'analysis': f"1-й слог '{s1['syllable_str']}' ({s1['length']}) + 2-й слог '{s2['syllable_str']}' ({s2['length']})"
                })
        
        elif result.get("mode") == "poetry":
            # 诗歌模式统计
            syllables = result['syllables']
            feet = result['feet']
            
            for syl in syllables:
                if syl.get('type') == 'открытый':
                    open_count += 1
                elif syl.get('type') == 'закрытый':
                    closed_count += 1

                if syl.get('length') == 'длинный':
                    long_count += 1
                elif syl.get('length') == 'короткий':
                    short_count += 1
            
            # 诗歌模式音步统计（使用自动划分的音步）
            for foot in feet:
                foot_key = foot['pattern']
                feet_counts[foot_key] = feet_counts.get(foot_key, 0) + 1
                
                syllable_strs = [s['syllable_str'] for s in foot['syllables']]
                full_syllable_str = "-".join(syllable_strs)
                
                feet_details.append({
                    'line': result['line'],
                    'syllable_pair': full_syllable_str,
                    'pattern': foot_key,
                    'name': foot['name'],
                    'name_local': foot['name'],
                    'length_symbols': foot['length_symbols'],
                    'analysis': f"音步模式 {foot_key} ({foot['name']})"
                })

    total_items = len(processed_results)
    total_syllables = open_count + closed_count

    sorted_feet = sorted(feet_counts.items(), key=lambda x: x[1], reverse=True)
    feet_labels = [item[0] for item in sorted_feet]
    feet_values = [item[1] for item in sorted_feet]

    return {
        'total_items': total_items,
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
        'word_table': word_table,  # Возвращаем новую таблицу для Prose
        'feet_names_map': FOOT_NAMES_MAP
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
    print(f"总单词数：{stats['total_items']} | 总音节数：{stats['total_syllables']}")
    print(f"开音节：{stats['open_count']} | 闭音节：{stats['closed_count']}")
    print(f"长音节：{stats['long_count']} | 短音节：{stats['short_count']}")
