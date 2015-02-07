Number::digits = (radix=10) ->
  digits = []
  i = 0
  loop
    upper_bound = Math.pow radix, i + 1
    current_radix = Math.pow radix, i
    digits.unshift ((@ % upper_bound) - (@ % current_radix)) / current_radix
    if upper_bound > @
      break
    i++
  digits

Number::abs = -> Math.abs @

Number::floor = -> Math.floor @
