import math

def format_height(value):
 try:
  number=float(value)
  if not math.isfinite(number):return '—'
  inches=int(math.floor(number+0.5));feet,remainder=divmod(inches,12)
  return f"{feet}′ {remainder}″"
 except (ValueError,TypeError):return '—'
