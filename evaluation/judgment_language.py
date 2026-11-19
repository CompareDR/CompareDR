"""Remove legacy forced-language instructions without adding a replacement."""
VERSION = 'judgment-language-v2-no-directive'

def without_forced_language(prompt):
    prompt = prompt.replace('Reasons in Chinese.', '')
    prompt = prompt.replace('"reason":"Chinese explanation"', '"reason":"explanation"')
    return prompt
