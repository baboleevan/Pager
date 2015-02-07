ONECOLOR = require 'one-color'

Number::to_color = ->
  new ONECOLOR "#{@toString 16}"

module.exports = ONECOLOR