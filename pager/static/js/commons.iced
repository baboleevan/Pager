_ = require 'underscore'
{observable} = require 'knockout'

throw_error = (err, next) ->
  throw err if err
  if next? and _.isFunction next
    next()

sum = (list) ->
  _.reduce list, (x, y) ->
    y = y + x
  , 0

_tics = {}
tic = (interval) ->
  t = _tics[interval]
  if not t
    t = _tics[interval] = observable new Date()
    setInterval ->
      t new Date
    , interval
  t

reversed = (array) ->
  array[..-1].reverse()

module.exports = {throw_error, sum, tic, reversed}