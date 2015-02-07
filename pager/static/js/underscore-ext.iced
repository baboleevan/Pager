_ = require 'underscore'

_.choice = (array) ->
  array[_.random 0, array.length - 1]

module.exports = _