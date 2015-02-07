{computed} = require 'knockout'

{Window} = require './window'


class Intro extends Window
  _template_name: 'intro'

  constructor: ->
    super

    @loading = computed =>
      windows = @windows()
      windows.length == 1 and windows[0] is this

module.exports = {Intro}