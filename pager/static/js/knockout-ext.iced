$ = require 'jquery'
_ = require 'underscore'
{computed, bindingHandlers, isObservable} = require 'knockout'
{unwrapObservable} = require('knockout').utils

require 'jquery-ext'
require 'vevent'
{log} = require 'logger'

bindingHandlers.scrollFix =
  init: (element) ->
    $(element).scrollFix()

bindingHandlers.placeholdIt = 
  init: (element) ->
    placeholder = element.placeholder
    $(element).focusin( ->
      element.placeholder = null
    ).focusout( ->
      element.placeholder = placeholder
    )

bindingHandlers.scrollTo =
  update: (element, valueAccessor) ->
    index = unwrapObservable valueAccessor()
    offset = $('.element', element).eq(index).offset()
    if offset
      $(element).animate {scrollTop: offset.top}, 300

bindingHandlers.scroll = 
  update: (element, valueAccessor) ->
    scroll = unwrapObservable valueAccessor()
    if scroll
      {index, duration, callback} = scroll
      if index is 0
        top = 0
      else
        top = ($('.element', element).eq(index).offset() ? {}).top
      if duration
        $(element).animate {scrollTop: top}, duration, callback
      else
        $(element).scrollTop top, callback

bindingHandlers.focus =
  init: (element, valueAccessor) ->
    observer = valueAccessor()
    if isObservable observer
      $(element).focus ->
        observer yes

bindingHandlers.force_transition = 
  init: (element, valueAccessor) ->
    force = unwrapObservable valueAccessor()
    if force
      _.defer_ ->
        height = $(element).height()
        $(element).height(0).css('min-height', 0)
        _.defer_ ->
          $(element).addClass('enable-transition')
          _.defer_ ->
            $(element).height(height)

bindingHandlers.fade_out = 
  update: (element, valueAccessor) ->
    value = unwrapObservable valueAccessor()
    if not value
      return
    element.transitionEnd = _.once ->
      delete element.transitionEnd
      $(element).hide().removeClass 'fade-out'
    $(element).show().addClass('fade-out')


bindingHandlers.push_down =
  init: (element) ->
    $e = $(element).vevent {events: ['vholdstart', 'vholdend']}
    $e.on 'vholdstart', (e) ->
      if e.currentTarget is element
        $e.addClass 'push-down'
    end = (e) ->
      if e.currentTarget is element
        $e.removeClass 'push-down'
    $e.on 'vholdend', end
    $e.on 'vholdcancel', end

bindingHandlers.background_color = 
  update: (element, valueAccessor) ->
    value = unwrapObservable valueAccessor()
    if _.isNumber value
      value = '#' + value.toString(16)
    $(element).css 'backgroundColor', value
