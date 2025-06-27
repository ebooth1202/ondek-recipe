from .base_imports import *


class CookingTechniqueExplainerTool:
    """Tool for explaining cooking techniques and terms using ChatGPT with Rupert's personality"""

    def __init__(self):
        self.name = "explain_cooking_technique"
        self.description = "Explain cooking techniques and culinary terms with Rupert's goofy personality"

    def detect_technique_question(self, user_message: str) -> Optional[str]:
        """Detect if user is asking about a cooking technique or term"""
        user_lower = user_message.lower().strip()

        question_indicators = [
            'what is', 'what does', 'how do i', 'how do you', 'how to', 'explain', 'define',
            'meaning of', 'technique', 'method', 'term', '?'
        ]

        has_question_pattern = any(indicator in user_lower for indicator in question_indicators)

        if not has_question_pattern:
            return None

        technique_map = {
            'sauté': ['saute', 'sautee', 'sautte', 'sauttee', 'sautteing', 'sauteing', 'sautéing'],
            'sautéing': ['sauteing', 'sautteing', 'sauteeing', 'sautting'],
            'braise': ['braising', 'braze', 'brazing'],
            'braising': ['brasing', 'brazing'],
            'julienne': ['julianne', 'julian', 'juliennes'],
            'dice': ['dicing', 'diced'],
            'chop': ['chopping', 'chopped'],
            'mince': ['mincing', 'minced'],
            'blanch': ['blanching', 'blanched'],
            'poach': ['poaching', 'poached'],
            'roast': ['roasting', 'roasted'],
            'grill': ['grilling', 'grilled'],
            'steam': ['steaming', 'steamed'],
            'fry': ['frying', 'fried'],
            'bake': ['baking', 'baked'],
            'broil': ['broiling', 'broiled'],
            'confit': ['confits', 'confiting'],
            'emulsify': ['emulsification', 'emulsifying'],
            'deglaze': ['deglazing', 'deglazed'],
            'roux': ['rouxs'],
            'mise en place': ['mise', 'mise-en-place', 'miseinplace'],
            'reduction': ['reduce', 'reducing'],
            'caramelize': ['caramelizing', 'caramelized', 'carmelize', 'carmelizing'],
            'sear': ['searing', 'seared'],
            'simmer': ['simmering', 'simmered'],
            'fold': ['folding', 'folded'],
            'whip': ['whipping', 'whipped'],
            'knead': ['kneading', 'kneaded'],
            'proof': ['proofing', 'proofed', 'prove', 'proving'],
            'tempering': ['temper', 'tempered'],
            'flambé': ['flambe', 'flaming', 'flame'],
            'sous vide': ['sousvide', 'sous-vide'],
            'marinade': ['marinating', 'marinated', 'marinate']
        }

        for base_technique, variations in technique_map.items():
            all_terms = [base_technique] + variations
            for term in all_terms:
                if term in user_lower:
                    logger.info(
                        f"Detected technique '{base_technique}' from term '{term}' in message: '{user_message}'")
                    return base_technique

        cooking_actions = [
            'cook', 'cooking', 'prepare', 'preparing', 'cut', 'cutting', 'heat', 'heating',
            'mix', 'mixing', 'stir', 'stirring', 'season', 'seasoning', 'salt', 'pepper'
        ]

        for action in cooking_actions:
            if action in user_lower and len(user_lower.split()) <= 6:
                logger.info(f"Detected cooking action '{action}' in question: '{user_message}'")
                return action

        return None

    async def execute(self, technique_term: str, user_message: str, openai_client) -> Optional[str]:
        """Generate explanation for cooking technique using ChatGPT"""
        try:
            if not openai_client:
                return None

            system_prompt = f"""You are Rupert, a jovial, warm, and delightfully goofy cooking assistant AI for the Ondek Recipe app.

The user is asking about the cooking technique/term: "{technique_term}"

Your job is to explain this cooking technique in Rupert's signature style:
- Be educational but fun and engaging
- Use goofy analogies and metaphors (food-related when possible)
- Show enthusiasm and warmth
- Include practical tips that are actually helpful
- Use emojis sparingly but effectively
- Keep it informative but not overwhelming
- Make cooking feel approachable and fun

Structure your response like this:
1. A fun, goofy explanation of what the technique is
2. Why it's useful or when to use it
3. A couple of practical tips
4. Maybe mention what dishes use this technique

Keep Rupert's personality: jovial, warm, goofy, encouraging, and passionate about making cooking accessible!"""

            user_prompt = f"""The user asked: "{user_message}"

They want to know about the cooking technique/term: "{technique_term}"

Explain this cooking technique with your signature Rupert personality - be educational, fun, and goofy!"""

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.8
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating technique explanation: {e}")
            return None