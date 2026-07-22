# PROMPT-PRECEDENCE

ترتیبِ اقتدار (`governance.PRECEDENCE`؛ اثبات: تست ۲، ۳):

    Constitution > Global Halt > Effect Policy > Memory Policy >
    Experiment Protocol > Operational Narrative > Agent Prompt > Retrieved Data

- `can_override(lower, higher)` فقط وقتی True که اقتدارِ lower اکیداً بیشتر باشد → عملاً
  لایهٔ پایین هرگز بالا را override نمی‌کند.
- **retrieved data** (متنِ بازیابی‌شده / ورودیِ نامعتمد) کمترین اقتدار را دارد؛ هرگز policy را
  override نمی‌کند (تست ۲) — هم‌راستا با context_fence (DATA_NOT_INSTRUCTION).
- **agent prompt** هرگز global halt را override نمی‌کند (تست ۳).
