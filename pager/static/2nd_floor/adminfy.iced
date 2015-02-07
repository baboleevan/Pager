_ = require 'underscore'

init = (callback=->) ->
  $ ->
    $('.focused').focus()
    $('.tooltiped').tooltip {}
    callback()

module.exports = init